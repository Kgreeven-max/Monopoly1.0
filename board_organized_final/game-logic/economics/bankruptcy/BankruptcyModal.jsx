import React, { useState, useEffect } from 'react';
import { useNotifications } from '../contexts/NotificationContext';
import { useGame } from '../contexts/GameContext';
import './BankruptcyModal.css';

const BankruptcyModal = ({ onClose }) => {
  const { state } = useGame();
  const { addNotification } = useNotifications();
  const [loading, setLoading] = useState(false);
  const [assets, setAssets] = useState({
    properties: [],
    loans: [],
    cds: [],
    helocs: [],
    cash: 0
  });
  const [debts, setDebts] = useState({
    loans: [],
    helocs: [],
    totalDebt: 0
  });
  const [loadingAssets, setLoadingAssets] = useState(true);
  
  // Get the player data from game state
  const playerData = state.players.find(p => p.id === state.currentPlayer?.id);
  
  // Calculate if bankruptcy is valid - player cannot pay their debts
  const [isBankruptcyValid, setIsBankruptcyValid] = useState(false);
  
  // Fetch player assets and debts
  useEffect(() => {
    const fetchAssetsAndDebts = async () => {
      if (!playerData) return;
      
      try {
        setLoadingAssets(true);
        
        // Fetch properties
        const propertiesResponse = await fetch(`/api/player/${playerData.id}/properties?pin=${playerData.pin}`);
        const propertiesData = await propertiesResponse.json();
        
        // Fetch loans, CDs, and HELOCs
        const financialsResponse = await fetch(`/api/finance/loans?player_id=${playerData.id}&pin=${playerData.pin}`);
        const financialsData = await financialsResponse.json();
        
        if (propertiesData.success && financialsData.success) {
          // Set assets
          const properties = propertiesData.properties || [];
          const loans = financialsData.loans.filter(l => l.loan_type === 'loan' && l.is_active) || [];
          const cds = financialsData.loans.filter(l => l.loan_type === 'cd' && l.is_active) || [];
          const helocs = financialsData.loans.filter(l => l.loan_type === 'heloc' && l.is_active) || [];
          
          // Calculate total property value
          const propertyValue = properties.reduce((sum, prop) => sum + prop.current_price, 0);
          
          // Calculate total CD value
          const cdValue = cds.reduce((sum, cd) => sum + cd.current_value, 0);
          
          // Calculate total debts
          const loanDebt = loans.reduce((sum, loan) => sum + loan.outstanding_balance, 0);
          const helocDebt = helocs.reduce((sum, heloc) => sum + heloc.outstanding_balance, 0);
          const totalDebt = loanDebt + helocDebt;
          
          // Total liquid assets
          const liquidAssets = playerData.cash + cdValue;
          
          // Set state
          setAssets({
            properties,
            loans,
            cds,
            helocs,
            cash: playerData.cash,
            propertyValue,
            cdValue,
            totalAssets: liquidAssets + propertyValue
          });
          
          setDebts({
            loans,
            helocs,
            loanDebt,
            helocDebt,
            totalDebt
          });
          
          // Determine if bankruptcy is valid
          setIsBankruptcyValid(liquidAssets < totalDebt && (liquidAssets + propertyValue) < totalDebt);
        }
      } catch (error) {
        addNotification({
          type: 'error',
          title: 'Error',
          message: 'Failed to fetch financial information',
          duration: 5000
        });
      } finally {
        setLoadingAssets(false);
      }
    };
    
    fetchAssetsAndDebts();
  }, [playerData, addNotification]);
  
  const handleDeclareBackruptcy = async () => {
    if (!isBankruptcyValid || loading) return;
    
    try {
      setLoading(true);
      
      const response = await fetch('/api/finance/bankruptcy', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          player_id: playerData.id,
          pin: playerData.pin
        }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        addNotification({
          type: 'info',
          title: 'Bankruptcy Declared',
          message: `You've been declared bankrupt. All your debts have been forgiven, but you've lost all your properties.`,
          duration: 7000
        });
        onClose();
      } else {
        addNotification({
          type: 'error',
          title: 'Bankruptcy Error',
          message: data.error || 'Failed to declare bankruptcy',
          duration: 5000
        });
      }
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Bankruptcy Error',
        message: 'Failed to process bankruptcy declaration',
        duration: 5000
      });
    } finally {
      setLoading(false);
    }
  };
  
  if (loadingAssets) {
    return (
      <div className="modal-backdrop">
        <div className="bankruptcy-modal">
          <div className="bankruptcy-modal-header">
            <h2>Analyzing Financial Status...</h2>
            <button className="close-button" onClick={onClose}>&times;</button>
          </div>
          <div className="bankruptcy-modal-content loading">
            <div className="spinner"></div>
            <p>Calculating assets and liabilities...</p>
          </div>
        </div>
      </div>
    );
  }
  
  if (!isBankruptcyValid) {
    return (
      <div className="modal-backdrop">
        <div className="bankruptcy-modal">
          <div className="bankruptcy-modal-header">
            <h2>Bankruptcy Not Allowed</h2>
            <button className="close-button" onClick={onClose}>&times;</button>
          </div>
          <div className="bankruptcy-modal-content">
            <div className="bankruptcy-info warning">
              <p>You have sufficient assets to pay your debts.</p>
              <p>Bankruptcy is only available when your debts exceed your total assets (cash, CDs, and properties).</p>
            </div>
            
            <div className="financial-summary">
              <div className="summary-section">
                <h3>Your Assets</h3>
                <div className="summary-item">
                  <span>Cash:</span>
                  <span className="value">${assets.cash}</span>
                </div>
                <div className="summary-item">
                  <span>CD Investments:</span>
                  <span className="value">${assets.cdValue || 0}</span>
                </div>
                <div className="summary-item">
                  <span>Property Value:</span>
                  <span className="value">${assets.propertyValue || 0}</span>
                </div>
                <div className="summary-item total">
                  <span>Total Assets:</span>
                  <span className="value">${assets.totalAssets || 0}</span>
                </div>
              </div>
              
              <div className="summary-section">
                <h3>Your Debts</h3>
                <div className="summary-item">
                  <span>Loans:</span>
                  <span className="value">${debts.loanDebt || 0}</span>
                </div>
                <div className="summary-item">
                  <span>HELOCs:</span>
                  <span className="value">${debts.helocDebt || 0}</span>
                </div>
                <div className="summary-item total">
                  <span>Total Debts:</span>
                  <span className="value">${debts.totalDebt || 0}</span>
                </div>
              </div>
            </div>
            
            <div className="modal-actions">
              <button className="cancel-button" onClick={onClose}>Close</button>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="modal-backdrop">
      <div className="bankruptcy-modal">
        <div className="bankruptcy-modal-header">
          <h2>Declare Bankruptcy</h2>
          <button className="close-button" onClick={onClose}>&times;</button>
        </div>
        
        <div className="bankruptcy-modal-content">
          <div className="bankruptcy-info">
            <p>You are eligible to declare bankruptcy because your debts exceed your total assets.</p>
            <p>This will clear all your debts, but you'll lose all your properties and investments.</p>
            <p>Your bankruptcy record will also affect future loan interest rates.</p>
          </div>
          
          <div className="bankruptcy-summary">
            <h3>Assets to be Forfeited</h3>
            
            <div className="summary-section">
              <h4>Properties ({assets.properties.length})</h4>
              {assets.properties.length > 0 ? (
                <div className="property-list">
                  {assets.properties.map(property => (
                    <div key={property.id} className="property-item">
                      <span>{property.name}</span>
                      <span className="value">${property.current_price}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-items">No properties</p>
              )}
            </div>
            
            <div className="summary-section">
              <h4>Investments ({assets.cds.length})</h4>
              {assets.cds.length > 0 ? (
                <div className="cd-list">
                  {assets.cds.map(cd => (
                    <div key={cd.id} className="cd-item">
                      <span>CD #{cd.id}</span>
                      <span className="value">${cd.current_value}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-items">No investments</p>
              )}
            </div>
            
            <h3>Debts to be Forgiven</h3>
            
            <div className="summary-section">
              <h4>Loans ({debts.loans.length})</h4>
              {debts.loans.length > 0 ? (
                <div className="loan-list">
                  {debts.loans.map(loan => (
                    <div key={loan.id} className="loan-item">
                      <span>Loan #{loan.id}</span>
                      <span className="value">${loan.outstanding_balance}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-items">No loans</p>
              )}
            </div>
            
            <div className="summary-section">
              <h4>HELOCs ({debts.helocs.length})</h4>
              {debts.helocs.length > 0 ? (
                <div className="heloc-list">
                  {debts.helocs.map(heloc => (
                    <div key={heloc.id} className="heloc-item">
                      <span>HELOC #{heloc.id} ({heloc.property?.name || 'Unknown'})</span>
                      <span className="value">${heloc.outstanding_balance}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-items">No HELOCs</p>
              )}
            </div>
            
            <div className="bankruptcy-totals">
              <div className="total-item">
                <span>Total Assets:</span>
                <span className="value">${assets.totalAssets || 0}</span>
              </div>
              <div className="total-item">
                <span>Total Debts:</span>
                <span className="value">${debts.totalDebt || 0}</span>
              </div>
              <div className="total-item deficit">
                <span>Deficit:</span>
                <span className="value">-${Math.max(0, debts.totalDebt - assets.totalAssets)}</span>
              </div>
            </div>
          </div>
          
          <div className="bankruptcy-warning">
            <p>Warning: After bankruptcy, you will start with $1,500 in cash, but no properties or investments.</p>
            <p>Your credit rating will be affected for the remainder of the game.</p>
          </div>
          
          <div className="modal-actions">
            <button className="cancel-button" onClick={onClose}>
              Cancel
            </button>
            <button
              className="bankruptcy-button"
              onClick={handleDeclareBackruptcy}
              disabled={loading}
            >
              {loading ? 'Processing...' : 'Declare Bankruptcy'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BankruptcyModal; 