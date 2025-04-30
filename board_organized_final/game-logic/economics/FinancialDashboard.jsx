import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import NewLoanModal from './NewLoanModal';
import CDCreationModal from './CDCreationModal';
import HELOCModal from './HELOCModal';
import BankruptcyModal from './BankruptcyModal';
import './FinancialDashboard.css';

const FinancialDashboard = ({ 
  playerId, 
  playerPin,
  playerCash,
  onTransactionComplete 
}) => {
  const [loans, setLoans] = useState([]);
  const [cds, setCds] = useState([]);
  const [helocs, setHelocs] = useState([]);
  const [interestRates, setInterestRates] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [showLoanModal, setShowLoanModal] = useState(false);
  const [showCDModal, setShowCDModal] = useState(false);
  const [showHELOCModal, setShowHELOCModal] = useState(false);
  const [showBankruptcyModal, setShowBankruptcyModal] = useState(false);

  // Fetch financial data
  useEffect(() => {
    const fetchFinancialData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch loans, CDs, and HELOCs
        const loansResponse = await fetch(
          `/api/finance/loans?player_id=${playerId}&pin=${playerPin}`
        );
        const loansData = await loansResponse.json();

        if (loansData.success) {
          setLoans(loansData.loans.filter(l => l.loan_type === 'loan'));
          setCds(loansData.loans.filter(l => l.loan_type === 'cd'));
          setHelocs(loansData.loans.filter(l => l.loan_type === 'heloc'));
        }

        // Fetch current interest rates
        const ratesResponse = await fetch('/api/finance/interest-rates');
        const ratesData = await ratesResponse.json();

        if (ratesData.success) {
          setInterestRates(ratesData.rates);
        }
      } catch (err) {
        setError('Failed to fetch financial data');
      } finally {
        setLoading(false);
      }
    };

    fetchFinancialData();
  }, [playerId, playerPin]);

  // Handle new loan creation
  const handleNewLoan = async (amount) => {
    try {
      const response = await fetch('/api/finance/loan/new', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          player_id: playerId,
          pin: playerPin,
          amount
        }),
      });

      const data = await response.json();
      if (data.success) {
        setLoans([...loans, data.loan]);
        onTransactionComplete();
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to create loan');
    }
  };

  // Handle new CD creation
  const handleNewCD = async (amount, lengthLaps) => {
    try {
      const response = await fetch('/api/finance/cd/new', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          player_id: playerId,
          pin: playerPin,
          amount,
          length_laps: lengthLaps
        }),
      });

      const data = await response.json();
      if (data.success) {
        setCds([...cds, data.cd]);
        onTransactionComplete();
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to create CD');
    }
  };

  // Handle loan repayment
  const handleRepayLoan = async (loanId, amount) => {
    try {
      const response = await fetch('/api/finance/loan/repay', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          player_id: playerId,
          pin: playerPin,
          loan_id: loanId,
          amount
        }),
      });

      const data = await response.json();
      if (data.success) {
        setLoans(loans.map(loan => 
          loan.id === loanId 
            ? { ...loan, outstanding_balance: data.remaining_balance, is_active: data.loan_status === 'active' }
            : loan
        ));
        onTransactionComplete();
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to repay loan');
    }
  };

  // Handle CD withdrawal
  const handleWithdrawCD = async (cdId) => {
    try {
      const response = await fetch('/api/finance/cd/withdraw', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          player_id: playerId,
          pin: playerPin,
          cd_id: cdId
        }),
      });

      const data = await response.json();
      if (data.success) {
        setCds(cds.filter(cd => cd.id !== cdId));
        onTransactionComplete();
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to withdraw CD');
    }
  };

  // Calculate total debt
  const totalDebt = loans.reduce((sum, loan) => 
    sum + (loan.is_active ? loan.outstanding_balance : 0), 0
  ) + helocs.reduce((sum, heloc) => 
    sum + (heloc.is_active ? heloc.outstanding_balance : 0), 0
  );

  // Calculate total investments
  const totalInvestments = cds.reduce((sum, cd) => 
    sum + (cd.is_active ? cd.current_value : 0), 0
  );

  // Calculate net worth
  const netWorth = playerCash + totalInvestments - totalDebt;

  // Check if player might be in financial distress
  const isInFinancialDistress = playerCash < totalDebt * 0.25 && totalDebt > 0;

  return (
    <div className="financial-dashboard">
      {/* Financial Overview */}
      <div className="financial-summary">
        <div className="summary-card cash">
          <h3>Cash</h3>
          <p className="amount">${playerCash}</p>
        </div>
        <div className="summary-card investments">
          <h3>Investments</h3>
          <p className="amount">${totalInvestments}</p>
        </div>
        <div className="summary-card debt">
          <h3>Total Debt</h3>
          <p className="amount">${totalDebt}</p>
        </div>
        <div className="summary-card net-worth">
          <h3>Net Worth</h3>
          <p className="amount">${netWorth}</p>
        </div>
      </div>

      {/* Bankruptcy Banner (only shows if in financial distress) */}
      {isInFinancialDistress && (
        <div className="bankruptcy-banner">
          <p>You appear to be in financial distress. If you can't pay your debts, bankruptcy may be an option.</p>
          <button 
            className="bankruptcy-button"
            onClick={() => setShowBankruptcyModal(true)}
          >
            Consider Bankruptcy
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="financial-tabs">
        <button 
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={`tab-button ${activeTab === 'loans' ? 'active' : ''}`}
          onClick={() => setActiveTab('loans')}
        >
          Loans
        </button>
        <button 
          className={`tab-button ${activeTab === 'investments' ? 'active' : ''}`}
          onClick={() => setActiveTab('investments')}
        >
          Investments
        </button>
        <button 
          className={`tab-button ${activeTab === 'heloc' ? 'active' : ''}`}
          onClick={() => setActiveTab('heloc')}
        >
          HELOC
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)} className="close-error">×</button>
        </div>
      )}

      {/* Content Area */}
      <div className="financial-content">
        {loading ? (
          <div className="loading-spinner">Loading financial data...</div>
        ) : (
          <>
            {activeTab === 'overview' && (
              <div className="financial-overview">
                <h3>Current Interest Rates</h3>
                {interestRates && (
                  <div className="rates-grid">
                    <div className="rate-card">
                      <h4>Loans</h4>
                      <p>{(interestRates.loan * 100).toFixed(1)}%</p>
                    </div>
                    <div className="rate-card">
                      <h4>CDs (3 Laps)</h4>
                      <p>{(interestRates.cd_3 * 100).toFixed(1)}%</p>
                    </div>
                    <div className="rate-card">
                      <h4>CDs (5 Laps)</h4>
                      <p>{(interestRates.cd_5 * 100).toFixed(1)}%</p>
                    </div>
                    <div className="rate-card">
                      <h4>CDs (7 Laps)</h4>
                      <p>{(interestRates.cd_7 * 100).toFixed(1)}%</p>
                    </div>
                    <div className="rate-card">
                      <h4>HELOC</h4>
                      <p>{(interestRates.heloc * 100).toFixed(1)}%</p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'loans' && (
              <div className="loans-section">
                <h3>Active Loans</h3>
                <div className="loans-grid">
                  {loans.filter(loan => loan.is_active).map(loan => (
                    <div key={loan.id} className="loan-card">
                      <div className="loan-header">
                        <h4>Loan #{loan.id}</h4>
                        <span className="loan-date">{new Date(loan.created_at).toLocaleDateString()}</span>
                      </div>
                      <div className="loan-details">
                        <p>Original Amount: ${loan.amount}</p>
                        <p>Current Balance: ${loan.outstanding_balance}</p>
                        <p>Interest Rate: {(loan.interest_rate * 100).toFixed(1)}%</p>
                        <p>Remaining Laps: {loan.remaining_laps}</p>
                      </div>
                      <button 
                        onClick={() => handleRepayLoan(loan.id, loan.outstanding_balance)}
                        className="repay-button"
                        disabled={playerCash < loan.outstanding_balance}
                      >
                        Repay Loan
                      </button>
                    </div>
                  ))}
                </div>
                <button 
                  onClick={() => setShowLoanModal(true)}
                  className="new-loan-button"
                >
                  Take New Loan
                </button>
              </div>
            )}

            {activeTab === 'investments' && (
              <div className="investments-section">
                <h3>Certificates of Deposit</h3>
                <div className="cd-grid">
                  {cds.filter(cd => cd.is_active).map(cd => (
                    <div key={cd.id} className="cd-card">
                      <div className="cd-header">
                        <h4>CD #{cd.id}</h4>
                        <span className="cd-date">{new Date(cd.created_at).toLocaleDateString()}</span>
                      </div>
                      <div className="cd-details">
                        <p>Principal: ${cd.amount}</p>
                        <p>Current Value: ${cd.current_value}</p>
                        <p>Interest Rate: {(cd.interest_rate * 100).toFixed(1)}%</p>
                        <p>Remaining Laps: {cd.remaining_laps}</p>
                      </div>
                      <button 
                        onClick={() => handleWithdrawCD(cd.id)}
                        className="withdraw-button"
                      >
                        Withdraw CD
                      </button>
                    </div>
                  ))}
                </div>
                <div className="new-cd-options">
                  <button onClick={() => setShowCDModal(true)} className="new-cd-button">
                    Create New CD
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'heloc' && (
              <div className="heloc-section">
                <h3>Home Equity Lines of Credit</h3>
                <div className="heloc-grid">
                  {helocs.filter(heloc => heloc.is_active).map(heloc => (
                    <div key={heloc.id} className="heloc-card">
                      <div className="heloc-header">
                        <h4>HELOC #{heloc.id}</h4>
                        <span className="heloc-date">{new Date(heloc.created_at).toLocaleDateString()}</span>
                      </div>
                      <div className="heloc-details">
                        <p>Property: {heloc.property?.name || 'Unknown'}</p>
                        <p>Original Amount: ${heloc.amount}</p>
                        <p>Current Balance: ${heloc.outstanding_balance}</p>
                        <p>Interest Rate: {(heloc.interest_rate * 100).toFixed(1)}%</p>
                      </div>
                      <button 
                        onClick={() => handleRepayLoan(heloc.id, heloc.outstanding_balance)}
                        className="repay-button"
                        disabled={playerCash < heloc.outstanding_balance}
                      >
                        Repay HELOC
                      </button>
                    </div>
                  ))}
                </div>
                <button 
                  onClick={() => setShowHELOCModal(true)}
                  className="new-heloc-button"
                >
                  Create New HELOC
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Modals */}
      {showLoanModal && (
        <NewLoanModal 
          onClose={() => setShowLoanModal(false)}
          onConfirm={handleNewLoan}
          playerCash={playerCash}
          interestRate={interestRates?.loan || 0.10}
          maxLoanAmount={5000}
        />
      )}

      {showCDModal && (
        <CDCreationModal 
          onClose={() => setShowCDModal(false)} 
        />
      )}

      {showHELOCModal && (
        <HELOCModal 
          onClose={() => setShowHELOCModal(false)} 
        />
      )}

      {showBankruptcyModal && (
        <BankruptcyModal 
          onClose={() => setShowBankruptcyModal(false)} 
        />
      )}
    </div>
  );
};

FinancialDashboard.propTypes = {
  playerId: PropTypes.number.isRequired,
  playerPin: PropTypes.string.isRequired,
  playerCash: PropTypes.number.isRequired,
  onTransactionComplete: PropTypes.func.isRequired
};

export default FinancialDashboard; 