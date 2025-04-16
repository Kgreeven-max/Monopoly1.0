import React, { useState } from 'react';
import PropTypes from 'prop-types';
import './NewLoanModal.css';

const NewLoanModal = ({ 
  onClose, 
  onConfirm, 
  playerCash, 
  interestRate,
  maxLoanAmount = 5000 
}) => {
  const [amount, setAmount] = useState(1000);
  const [error, setError] = useState(null);

  // Calculate monthly payment (simplified)
  const calculatePayment = (loanAmount) => {
    // Using simple interest for 5 laps
    const totalInterest = loanAmount * interestRate * 5;
    const totalAmount = loanAmount + totalInterest;
    return Math.ceil(totalAmount / 5);  // Payment per lap
  };

  const handleAmountChange = (e) => {
    const value = parseInt(e.target.value, 10);
    if (isNaN(value)) {
      setError('Please enter a valid number');
      return;
    }
    if (value > maxLoanAmount) {
      setError(`Maximum loan amount is $${maxLoanAmount}`);
      setAmount(maxLoanAmount);
      return;
    }
    if (value < 100) {
      setError('Minimum loan amount is $100');
      setAmount(100);
      return;
    }
    setAmount(value);
    setError(null);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (amount < 100 || amount > maxLoanAmount) {
      return;
    }
    onConfirm(amount);
  };

  const paymentPerLap = calculatePayment(amount);
  const totalPayment = paymentPerLap * 5;
  const totalInterest = totalPayment - amount;

  return (
    <div className="modal-overlay">
      <div className="loan-modal">
        <header className="modal-header">
          <h2>Take Out a New Loan</h2>
          <button onClick={onClose} className="close-button">×</button>
        </header>

        <form onSubmit={handleSubmit} className="loan-form">
          <div className="form-group">
            <label htmlFor="loan-amount">Loan Amount:</label>
            <div className="amount-input">
              <span className="currency-symbol">$</span>
              <input
                type="number"
                id="loan-amount"
                value={amount}
                onChange={handleAmountChange}
                min="100"
                max={maxLoanAmount}
                step="100"
              />
            </div>
            {error && <span className="error-text">{error}</span>}
          </div>

          <div className="loan-details">
            <div className="detail-row">
              <span>Interest Rate:</span>
              <span>{(interestRate * 100).toFixed(1)}%</span>
            </div>
            <div className="detail-row">
              <span>Loan Term:</span>
              <span>5 Laps</span>
            </div>
            <div className="detail-row">
              <span>Payment per Lap:</span>
              <span>${paymentPerLap}</span>
            </div>
            <div className="detail-row total">
              <span>Total Interest:</span>
              <span>${totalInterest}</span>
            </div>
            <div className="detail-row total">
              <span>Total Payment:</span>
              <span>${totalPayment}</span>
            </div>
          </div>

          <div className="loan-warnings">
            <p className="warning-text">
              ⚠️ Failure to make payments may result in property liens or bankruptcy.
            </p>
            <p className="info-text">
              💡 Payments are automatically deducted when passing GO.
            </p>
          </div>

          <div className="modal-footer">
            <button 
              type="button" 
              onClick={onClose}
              className="cancel-button"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="confirm-button"
              disabled={!!error || amount < 100 || amount > maxLoanAmount}
            >
              Take Loan
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

NewLoanModal.propTypes = {
  onClose: PropTypes.func.isRequired,
  onConfirm: PropTypes.func.isRequired,
  playerCash: PropTypes.number.isRequired,
  interestRate: PropTypes.number.isRequired,
  maxLoanAmount: PropTypes.number
};

export default NewLoanModal; 