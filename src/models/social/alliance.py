from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models import db
import uuid

class Alliance(db.Model):
    """Player alliance model"""
    __tablename__ = 'alliances'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('players.id'))
    status = db.Column(db.String(20), default='active')  # active, disbanded
    
    # Alliance benefit settings
    rent_discount = db.Column(db.Float, default=0.1)  # 10% rent discount between members
    development_discount = db.Column(db.Float, default=0.0)  # No development discount initially
    
    # Optional associated chat channel
    chat_channel_id = db.Column(db.String(36), db.ForeignKey('channels.id'))
    
    # Relationships
    members = db.relationship('AllianceMember', backref='alliance', lazy='dynamic', cascade='all, delete-orphan')
    invites = db.relationship('AllianceInvite', backref='alliance', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert alliance to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'status': self.status,
            'benefits': {
                'rent_discount': self.rent_discount,
                'development_discount': self.development_discount
            },
            'chat_channel_id': self.chat_channel_id,
            'member_count': self.members.filter_by(status='active').count()
        }
    
    def is_member(self, player_id):
        """Check if player is a member of this alliance"""
        return AllianceMember.query.filter_by(
            alliance_id=self.id, player_id=player_id, status='active').first() is not None
    
    def add_member(self, player_id, role='member'):
        """Add a player to this alliance"""
        if not self.is_member(player_id):
            # Check if there's an existing inactive membership
            existing = AllianceMember.query.filter_by(
                alliance_id=self.id, player_id=player_id).first()
            
            if existing:
                # Reactivate existing membership
                existing.status = 'active'
                existing.role = role
                existing.joined_at = datetime.utcnow()
            else:
                # Create new membership
                member = AllianceMember(
                    alliance_id=self.id, 
                    player_id=player_id,
                    role=role
                )
                db.session.add(member)
            
            return True
        return False
    
    def remove_member(self, player_id):
        """Remove a player from this alliance"""
        member = AllianceMember.query.filter_by(
            alliance_id=self.id, player_id=player_id, status='active').first()
        
        if member:
            # Set status to inactive rather than deleting
            member.status = 'inactive'
            member.left_at = datetime.utcnow()
            return True
        return False


class AllianceMember(db.Model):
    """Alliance membership model"""
    __tablename__ = 'alliance_members'
    
    id = db.Column(db.Integer, primary_key=True)
    alliance_id = db.Column(db.String(36), db.ForeignKey('alliances.id'), nullable=False)
    player_id = db.Column(db.String(36), db.ForeignKey('players.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # member, officer, leader
    status = db.Column(db.String(20), default='active')  # active, inactive
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    left_at = db.Column(db.DateTime)
    
    # Unique constraint for active memberships
    __table_args__ = (
        db.UniqueConstraint('alliance_id', 'player_id', 'status', name='unique_active_alliance_membership'),
    )
    
    def to_dict(self):
        """Convert membership to dictionary"""
        return {
            'id': self.id,
            'alliance_id': self.alliance_id,
            'player_id': self.player_id,
            'role': self.role,
            'status': self.status,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'left_at': self.left_at.isoformat() if self.left_at else None
        }


class AllianceInvite(db.Model):
    """Alliance invitation model"""
    __tablename__ = 'alliance_invites'
    
    id = db.Column(db.Integer, primary_key=True)
    alliance_id = db.Column(db.String(36), db.ForeignKey('alliances.id'), nullable=False)
    player_id = db.Column(db.String(36), db.ForeignKey('players.id'), nullable=False)
    inviter_id = db.Column(db.String(36), db.ForeignKey('players.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, declined, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    # Unique constraint to prevent duplicate invites
    __table_args__ = (
        db.UniqueConstraint('alliance_id', 'player_id', 'status', name='unique_pending_alliance_invite'),
    )
    
    def to_dict(self):
        """Convert invite to dictionary"""
        return {
            'id': self.id,
            'alliance_id': self.alliance_id,
            'player_id': self.player_id,
            'inviter_id': self.inviter_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
    
    def accept(self):
        """Accept this alliance invitation"""
        if self.status == 'pending':
            self.status = 'accepted'
            self.resolved_at = datetime.utcnow()
            
            # Add player to alliance
            alliance = Alliance.query.get(self.alliance_id)
            if alliance:
                alliance.add_member(self.player_id)
            
            return True
        return False
    
    def decline(self):
        """Decline this alliance invitation"""
        if self.status == 'pending':
            self.status = 'declined'
            self.resolved_at = datetime.utcnow()
            return True
        return False
    
    def cancel(self):
        """Cancel this alliance invitation"""
        if self.status == 'pending':
            self.status = 'cancelled'
            self.resolved_at = datetime.utcnow()
            return True
        return False 