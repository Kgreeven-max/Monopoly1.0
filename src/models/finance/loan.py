from datetime import datetime
import json
from typing import Dict, List, Optional, Union, Any
import logging

from src.models import db
from src.models.player import Player
from src.models.property import Property

# Set up logger
logger = logging.getLogger(__name__)

class Loan(db.Model):
    """Model for player loans, CDs, and HELOCs"""
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    start_lap = db.Column(db.Integer, nullable=False)
    length_laps = db.Column(db.Integer, nullable=False)
    loan_type = db.Column(db.String(20), nullable=False, default="loan")  # "loan", "cd", "heloc"
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=True)  # For HELOC
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    original_interest_rate = db.Column(db.Float, nullable=True)  # Store original rate for tracking changes
    outstanding_balance = db.Column(db.Integer, nullable=False)  # Current balance with interest
    
    # Relationships
    property = db.relationship('Property', backref='loans', lazy=True)
    
    def __repr__(self):
        return f'<{self.loan_type.capitalize()} {self.id}: ${self.amount} for Player {self.player_id}>'
    
    def to_dict(self):
        """Convert loan to dictionary for API responses"""
        return {
            'id': self.id,
            'player_id': self.player_id,
            'amount': self.amount,
            'interest_rate': self.interest_rate,
            'start_lap': self.start_lap,
            'length_laps': self.length_laps,
            'loan_type': self.loan_type,
            'property_id': self.property_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'original_interest_rate': self.original_interest_rate or self.interest_rate,
            'outstanding_balance': self.outstanding_balance
        }
    
    def calculate_remaining_laps(self, current_lap: int):
        """Calculate remaining laps until loan/CD completion"""
        if current_lap is None:
            raise ValueError("current_lap must be provided")
        
        return max(0, self.start_lap + self.length_laps - current_lap)
    
    def calculate_current_value(self, current_lap: int):
        """Calculate current value of loan/CD with interest"""
        if current_lap is None:
            raise ValueError("current_lap must be provided")
        
        # Calculate laps that have passed
        laps_passed = max(0, current_lap - self.start_lap)
        
        if self.loan_type == "cd":
            # For CDs, calculate interest earned
            value = self.amount * (1 + self.interest_rate) ** laps_passed
        else:
            # For loans and HELOCs, return the current outstanding balance.
            # Interest accrual happens separately via accrue_interest().
            value = self.outstanding_balance
        
        return int(value)
        
    def accrue_interest(self):
        """Accrue interest for one lap for active loans/HELOCs."""
        if not self.is_active or self.loan_type == "cd":
            return # Only accrue for active loans/HELOCs
        
        interest_amount = self.outstanding_balance * self.interest_rate
        # Ensure balance remains an integer
        self.outstanding_balance = int(self.outstanding_balance + interest_amount)
        logger.info(f"Accrued interest {int(interest_amount)} for {self.loan_type} {self.id}. New balance: {self.outstanding_balance}")
        
        # Note: db.session.commit() should be handled by the calling process
        # after iterating through all loans for the lap.
        db.session.add(self)
        
    def adjust_interest_rate(self, change_amount):
        """
        Adjust the interest rate of this loan or CD
        
        Args:
            change_amount: The amount to change the interest rate by (positive or negative)
        
        Returns:
            The new interest rate
        """
        # Store original rate if not already saved
        if self.original_interest_rate is None:
            self.original_interest_rate = self.interest_rate
            
        # Calculate new rate
        new_rate = max(0.01, self.interest_rate + change_amount)  # Ensure minimum 1% rate
        
        # Apply the new rate
        self.interest_rate = new_rate
        db.session.add(self)
        
        # Log the change
        logger.info(f"Adjusted {self.loan_type} #{self.id} interest rate from {self.original_interest_rate} to {new_rate}")
        
        return new_rate
        
    def repay(self, amount):
        """
        Repay some or all of a loan
        
        Args:
            amount: Amount to repay
            
        Returns:
            Dictionary with repayment results
        """
        # Don't allow repaying CDs (use withdraw instead)
        if self.loan_type == "cd":
            return {
                "success": False,
                "error": "Cannot repay a CD. Use withdraw instead."
            }
            
        # Check if loan is already paid off
        if not self.is_active:
            return {
                "success": False,
                "error": "This loan is already paid off."
            }
            
        # Get current balance (interest should already be accrued)
        current_balance = self.outstanding_balance
        
        # Handle full repayment
        if amount >= current_balance:
            repaid_amount = current_balance
            overpayment = amount - current_balance
            self.outstanding_balance = 0
            self.is_active = False
            db.session.add(self)
            
            return {
                "success": True,
                "amount_paid": repaid_amount,
                "overpayment": overpayment,
                "loan_id": self.id,
                "loan_status": "paid",
                "remaining_balance": 0
            }
            
        # Handle partial repayment
        self.outstanding_balance = current_balance - amount
        db.session.add(self)
        
        return {
            "success": True,
            "amount_paid": amount,
            "overpayment": 0,
            "loan_id": self.id,
            "loan_status": "active",
            "remaining_balance": self.outstanding_balance
        }
        
    def withdraw_cd(self, is_mature=False):
        """
        Withdraw a CD
        
        Args:
            is_mature: Whether the CD has reached maturity
            
        Returns:
            Dictionary with withdrawal results
        """
        # Only applicable to CDs
        if self.loan_type != "cd":
            return {
                "success": False,
                "error": "Not a Certificate of Deposit."
            }
            
        # Check if CD is already withdrawn
        if not self.is_active:
            return {
                "success": False,
                "error": "This CD has already been withdrawn."
            }
            
        # Calculate current value
        current_value = self.calculate_current_value(current_lap=None)
        
        # Apply early withdrawal penalty if not mature
        if not is_mature:
            penalty_rate = 0.10  # 10% penalty
            penalty_amount = int(current_value * penalty_rate)
            withdrawal_amount = current_value - penalty_amount
        else:
            penalty_amount = 0
            withdrawal_amount = current_value
            
        # Complete withdrawal
        self.is_active = False
        db.session.add(self)
        
        return {
            "success": True,
            "withdrawal_amount": withdrawal_amount,
            "penalty_amount": penalty_amount,
            "cd_id": self.id,
            "cd_status": "withdrawn",
            "was_mature": is_mature
        }
        
    @classmethod
    def create_loan(cls, player_id, amount, interest_rate, length_laps, current_lap, loan_type="loan", property_id=None):
        """Create a new loan, CD, or HELOC"""
        loan = cls(
            player_id=player_id,
            amount=amount,
            interest_rate=interest_rate,
            original_interest_rate=interest_rate,
            start_lap=current_lap,
            length_laps=length_laps,
            loan_type=loan_type,
            property_id=property_id,
            is_active=True,
            outstanding_balance=amount
        )
        
        db.session.add(loan)
        return loan
        
    @classmethod
    def get_active_loans_for_player(cls, player_id):
        """Get all active loans for a player"""
        return cls.query.filter_by(
            player_id=player_id,
            is_active=True,
            loan_type="loan"
        ).all()
        
    @classmethod
    def get_active_cds_for_player(cls, player_id):
        """Get all active CDs for a player"""
        return cls.query.filter_by(
            player_id=player_id,
            is_active=True,
            loan_type="cd"
        ).all()
        
    @classmethod
    def get_active_helocs_for_player(cls, player_id):
        """Get all active HELOCs for a player"""
        return cls.query.filter_by(
            player_id=player_id,
            is_active=True,
            loan_type="heloc"
        ).all()
        
    @classmethod
    def get_active_loans_for_property(cls, property_id):
        """Get all active HELOCs for a property"""
        return cls.query.filter_by(
            property_id=property_id,
            is_active=True,
            loan_type="heloc"
        ).all() 