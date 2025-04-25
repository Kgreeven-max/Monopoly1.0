// Finance Tab Functions

// Function to initialize the finance tab
function initializeFinanceTab() {
    console.log('Initializing finance tab...');
    refreshFinancialOverview();
    refreshLoans();
    refreshTransactions();
    loadEconomicState();
}

// Function to refresh the financial overview
function refreshFinancialOverview() {
    console.log('Refreshing financial overview...');
    
    fetch('/api/admin/finance/overview', {
        method: 'GET',
        headers: {
            'X-Admin-Key': window.adminKey
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Update financial stats
            const statsElement = document.getElementById('finance-stats');
            if (statsElement) {
                // Check if stats exists before trying to access properties
                const stats = data.stats || {};
                
                let statsHtml = `
                    <table class="table">
                        <tr><th>Total Money in Game:</th><td>$${stats.total_money || 0}</td></tr>
                        <tr><th>Bank Reserves:</th><td>$${stats.bank_reserves || 0}</td></tr>
                        <tr><th>Player Holdings:</th><td>$${stats.player_holdings || 0}</td></tr>
                        <tr><th>Community Fund:</th><td>$${stats.community_fund || 0}</td></tr>
                        <tr><th>Total Active Loans:</th><td>$${stats.loans_total || 0}</td></tr>
                    </table>
                `;
                statsElement.innerHTML = statsHtml;
            }
            
            // Update interest rates
            const ratesElement = document.getElementById('interest-rates');
            if (ratesElement) {
                const rates = data.rates || {};
                
                let ratesHtml = `
                    <table class="table">
                        <tr><th>Base Interest Rate:</th><td>${(rates.base_rate * 100).toFixed(2)}%</td></tr>
                        <tr><th>Loan Rate:</th><td>${((rates.rates?.loan?.standard || 0) * 100).toFixed(2)}%</td></tr>
                        <tr><th>Savings Rate:</th><td>${((rates.rates?.cd?.medium_term || 0) * 100).toFixed(2)}%</td></tr>
                        <tr><th>Mortgage Rate:</th><td>${((rates.rates?.heloc || 0) * 100).toFixed(2)}%</td></tr>
                    </table>
                `;
                ratesElement.innerHTML = ratesHtml;
            }
        } else {
            console.error('Failed to refresh financial overview:', data.error);
            // Provide fallback content when there's an error
            provideFallbackFinancialData();
        }
    })
    .catch(error => {
        console.error('Error refreshing financial overview:', error);
        
        // Provide fallback content
        provideFallbackFinancialData();
    });
}

// Function to provide fallback financial data when API fails
function provideFallbackFinancialData() {
    // Update financial stats with fallback content
    const statsElement = document.getElementById('finance-stats');
    if (statsElement) {
        statsElement.innerHTML = `
            <div class="alert alert-warning">
                <p>Financial data unavailable. Unable to connect to financial system.</p>
                <button class="btn btn-sm btn-primary mt-2" onclick="refreshFinancialOverview()">
                    <i class="bi bi-arrow-repeat"></i> Try Again
                </button>
            </div>
        `;
    }
    
    // Update interest rates with fallback content
    const ratesElement = document.getElementById('interest-rates');
    if (ratesElement) {
        ratesElement.innerHTML = `
            <div class="alert alert-warning">
                <p>Interest rate data unavailable. Unable to connect to financial system.</p>
                <button class="btn btn-sm btn-primary mt-2" onclick="refreshFinancialOverview()">
                    <i class="bi bi-arrow-repeat"></i> Try Again
                </button>
            </div>
        `;
    }
}

// Function to refresh active loans
function refreshLoans() {
    console.log('Refreshing active loans...');
    
    // Fetch regular loans
    fetch('/api/admin/finance/loans', {
        method: 'GET',
        headers: {
            'X-Admin-Key': window.adminKey
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Loans API response:', data);
        
        if (data.success) {
            // Update loans table
            const loansElement = document.getElementById('active-loans');
            if (loansElement) {
                // Filter to only regular loans, not CDs or HELOCs
                const loans = (data.loans || []).filter(loan => loan.loan_type === 'loan');
                console.log(`Found ${loans.length} regular loans`);
                
                if (loans.length === 0) {
                    loansElement.innerHTML = '<p class="text-center">No active loans found.</p>';
                }
                else {
                    let loansHtml = `
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Player</th>
                                        <th>Amount</th>
                                        <th>Interest</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                    `;
                    
                    loans.forEach(loan => {
                        loansHtml += `
                            <tr>
                                <td>${loan.id}</td>
                                <td>${loan.player_name || 'Unknown'}</td>
                                <td>$${loan.outstanding_balance}</td>
                                <td>${((loan.interest_rate || 0) * 100).toFixed(2)}%</td>
                                <td>${loan.is_active ? 'Active' : 'Paid'}</td>
                                <td>
                                    <button class="btn btn-sm btn-primary" onclick="viewLoanDetails(${loan.id})">View</button>
                                    <button class="btn btn-sm btn-success" onclick="repayLoan(${loan.id})">Repay</button>
                                </td>
                            </tr>
                        `;
                    });
                    
                    loansHtml += `
                                </tbody>
                            </table>
                        </div>
                    `;
                    
                    loansElement.innerHTML = loansHtml;
                }
            }
            
            // Call the specific endpoint for CDs
            refreshActiveCDs();
            
            // Update HELOCs table if needed
            const helocsElement = document.getElementById('active-helocs');
            if (helocsElement) {
                // Filter to only HELOCs
                const helocs = (data.loans || []).filter(loan => loan.loan_type === 'heloc' && loan.is_active);
                
                if (helocs.length === 0) {
                    helocsElement.innerHTML = '<p class="text-center">No active home equity lines of credit found.</p>';
                }
                else {
                    let helocsHtml = `
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Player</th>
                                        <th>Property</th>
                                        <th>Balance</th>
                                        <th>Interest</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                    `;
                    
                    helocs.forEach(heloc => {
                        helocsHtml += `
                            <tr>
                                <td>${heloc.id}</td>
                                <td>${heloc.player_name || 'Unknown'}</td>
                                <td>${heloc.property_name || 'Unknown'}</td>
                                <td>$${heloc.outstanding_balance}</td>
                                <td>${((heloc.interest_rate || 0) * 100).toFixed(2)}%</td>
                                <td>
                                    <button class="btn btn-sm btn-primary" onclick="viewLoanDetails(${heloc.id})">View</button>
                                    <button class="btn btn-sm btn-success" onclick="repayLoan(${heloc.id})">Repay</button>
                                </td>
                            </tr>
                        `;
                    });
                    
                    helocsHtml += `
                                </tbody>
                            </table>
                        </div>
                    `;
                    
                    helocsElement.innerHTML = helocsHtml;
                }
            }
        } else {
            console.error("Failed to load loans:", data.error);
        }
    })
    .catch(error => {
        console.error('Error refreshing loans:', error);
        
        // Provide fallback content
        const loansElement = document.getElementById('active-loans');
        if (loansElement) {
            loansElement.innerHTML = '<p class="text-center">Error loading loans data. Please check the console for details.</p>';
        }
        
        refreshActiveCDs(); // Still try to load CDs separately
        
        const helocsElement = document.getElementById('active-helocs');
        if (helocsElement) {
            helocsElement.innerHTML = '<p class="text-center">Error loading HELOCs data. Please check the console for details.</p>';
        }
    });
}

// New function to specifically fetch active CDs
function refreshActiveCDs() {
    console.log('Refreshing active CDs...');
    const cdsElement = document.getElementById('active-cds');
    
    if (!cdsElement) {
        console.error('CD element not found in DOM');
        return;
    }
    
    // Show loading indicator
    cdsElement.innerHTML = '<p class="text-center">Loading certificates of deposit...</p>';
    
    // Use the loans endpoint since the /active-cds endpoint is returning 404
    fetch('/api/admin/finance/loans', {
        method: 'GET',
        headers: {
            'X-Admin-Key': window.adminKey
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Using loans endpoint for CDs');
        
        if (data.success) {
            // Filter to only active CDs
            const cds = (data.loans || []).filter(loan => loan.loan_type === 'cd' && loan.is_active);
            console.log(`Found ${cds.length} CDs from loans endpoint`, cds);
            
            if (cds.length === 0) {
                cdsElement.innerHTML = '<p class="text-center">No active certificates of deposit found.</p>';
            } else {
                let cdsHtml = `
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Player</th>
                                    <th>Amount</th>
                                    <th>Interest</th>
                                    <th>Term</th>
                                    <th>Maturity</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                cds.forEach(cd => {
                    // Calculate display values with fallbacks
                    const termLength = cd.length_laps || cd.term || 0;
                    const maturityLap = cd.maturity_lap || (cd.start_lap + termLength);
                    
                    console.log(`CD ${cd.id}: length_laps=${termLength}, maturity_lap=${maturityLap}`);
                    
                    cdsHtml += `
                        <tr>
                            <td>${cd.id}</td>
                            <td>${cd.player_name || 'Player ' + cd.player_id}</td>
                            <td>$${cd.amount || cd.outstanding_balance}</td>
                            <td>${((cd.interest_rate || 0) * 100).toFixed(2)}%</td>
                            <td>${termLength} laps</td>
                            <td>Lap ${maturityLap}</td>
                            <td>
                                <button class="btn btn-sm btn-primary" onclick="viewLoanDetails(${cd.id})">View</button>
                                <button class="btn btn-sm btn-success" onclick="withdrawCD(${cd.id})">Withdraw</button>
                            </td>
                        </tr>
                    `;
                });
                
                cdsHtml += `
                            </tbody>
                        </table>
                    </div>
                `;
                
                cdsElement.innerHTML = cdsHtml;
                console.log('CD table updated successfully');
            }
        } else {
            console.error('Failed to load CDs:', data.error);
            cdsElement.innerHTML = '<p class="text-center">Error loading CD data. Please check the console for details.</p>';
        }
    })
    .catch(error => {
        console.error('Error refreshing CDs:', error);
        cdsElement.innerHTML = '<p class="text-center">Error loading CDs. Please check the console for details.</p>';
    });
}

// Function to refresh recent transactions
function refreshTransactions() {
    console.log('Refreshing recent transactions...');
    
    fetch('/api/admin/finance/transactions', {
        method: 'GET',
        headers: {
            'X-Admin-Key': window.adminKey
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Transactions data received:', data);
        if (data.success) {
            // Update transactions table
            const transactionsElement = document.getElementById('transactions-table');
            if (transactionsElement) {
                const transactions = data.transactions || [];
                
                if (transactions.length === 0) {
                    transactionsElement.innerHTML = '<tr><td colspan="6" class="text-center">No recent transactions found.</td></tr>';
                    return;
                }
                
                let transactionsHtml = '';
                
                transactions.forEach(tx => {
                    // Format transaction data with fallbacks
                    const timestamp = tx.timestamp || new Date().toISOString();
                    const type = tx.transaction_type || tx.type || 'N/A';
                    const from = tx.from_player_name || (tx.from_player_id ? `Player ${tx.from_player_id}` : 'Bank');
                    const to = tx.to_player_name || (tx.to_player_id ? `Player ${tx.to_player_id}` : 'Bank');
                    const description = tx.description || tx.reason || '';
                    
                    transactionsHtml += `
                        <tr>
                            <td>${formatDate(timestamp)}</td>
                            <td>${type}</td>
                            <td>${from}</td>
                            <td>${to}</td>
                            <td>$${tx.amount}</td>
                            <td>${description}</td>
                        </tr>
                    `;
                });
                
                transactionsElement.innerHTML = transactionsHtml;
                console.log(`Rendered ${transactions.length} transactions`);
            }
        } else {
            console.error('Failed to refresh transactions:', data.error);
            // Provide fallback content when there's an error
            const transactionsElement = document.getElementById('transactions-table');
            if (transactionsElement) {
                transactionsElement.innerHTML = '<tr><td colspan="6" class="text-center">Error loading transaction data. Please check the console for details.</td></tr>';
            }
        }
    })
    .catch(error => {
        console.error('Error refreshing transactions:', error);
        
        // Provide fallback content
        const transactionsElement = document.getElementById('transactions-table');
        if (transactionsElement) {
            transactionsElement.innerHTML = '<tr><td colspan="6" class="text-center">Error loading transaction data. Please check the console for details.</td></tr>';
        }
    });
}

// Function to load economic state
function loadEconomicState() {
    console.log('Loading economic state...');
    
    fetch('/api/admin/economic/state', {
        method: 'GET',
        headers: {
            'X-Admin-Key': window.adminKey
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Update economic state info
            const economicElement = document.getElementById('economy-info');
            if (economicElement) {
                const state = data.economic_state || {};
                
                let stateHtml = `
                    <table class="table">
                        <tr>
                            <th>Current State:</th>
                            <td><span class="badge bg-primary">${state.current_state || 'normal'}</span></td>
                        </tr>
                        <tr>
                            <th>Description:</th>
                            <td>${state.state_description || 'Standard economic conditions'}</td>
                        </tr>
                        <tr>
                            <th>Inflation Rate:</th>
                            <td>${((state.inflation_rate || 0) * 100).toFixed(2)}%</td>
                        </tr>
                        <tr>
                            <th>Base Interest Rate:</th>
                            <td>${((state.base_interest_rate || 0.05) * 100).toFixed(2)}%</td>
                        </tr>
                        <tr>
                            <th>Last Updated:</th>
                            <td>${state.last_cycle_update || 'Never'}</td>
                        </tr>
                    </table>
                `;
                
                economicElement.innerHTML = stateHtml;
            }
        } else {
            console.error('Error loading economic state:', data.error);
        }
    })
    .catch(error => {
        console.error('Error loading economic state:', error);
        
        // Provide fallback content
        const economicElement = document.getElementById('economy-info');
        if (economicElement) {
            economicElement.innerHTML = '<p class="text-center">Error loading economic data.</p>';
        }
    });
}

// Utility functions for loan management
function viewLoanDetails(loanId) {
    console.log('View loan details for loan ID:', loanId);
    
    fetch(`/api/admin/finance/loans/${loanId}`, {
        method: 'GET',
        headers: {
            'X-Admin-Key': window.adminKey
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Display loan details in a modal
            const loan = data.loan;
            const modalContent = `
                <div class="modal-header">
                    <h5 class="modal-title">Loan Details: #${loan.id}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <table class="table">
                        <tr><th>Player:</th><td>${loan.player_name}</td></tr>
                        <tr><th>Principal Amount:</th><td>$${loan.principal}</td></tr>
                        <tr><th>Current Balance:</th><td>$${loan.balance}</td></tr>
                        <tr><th>Interest Rate:</th><td>${(loan.interest_rate * 100).toFixed(2)}%</td></tr>
                        <tr><th>Start Date:</th><td>${loan.start_date}</td></tr>
                        <tr><th>Due Date:</th><td>${loan.due_date}</td></tr>
                        <tr><th>Payments Made:</th><td>${loan.payments_made}</td></tr>
                        <tr><th>Payments Remaining:</th><td>${loan.payments_remaining}</td></tr>
                        <tr><th>Status:</th><td>${loan.status}</td></tr>
                    </table>
                    <h6>Payment Schedule</h6>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Payment #</th>
                                    <th>Due Date</th>
                                    <th>Amount</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${(loan.payment_schedule || []).map((payment, index) => `
                                    <tr>
                                        <td>${index + 1}</td>
                                        <td>${payment.due_date}</td>
                                        <td>$${payment.amount}</td>
                                        <td>${payment.paid ? 'Paid' : 'Pending'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button type="button" class="btn btn-warning" onclick="extendLoan(${loan.id})">Extend Loan</button>
                    <button type="button" class="btn btn-success" onclick="payoffLoan(${loan.id})">Payoff Loan</button>
                </div>
            `;
            
            // Find or create the modal
            let loanModal = document.getElementById('loan-details-modal');
            
            if (!loanModal) {
                loanModal = document.createElement('div');
                loanModal.className = 'modal fade';
                loanModal.id = 'loan-details-modal';
                loanModal.setAttribute('tabindex', '-1');
                loanModal.setAttribute('aria-labelledby', 'loan-details-modal-label');
                loanModal.setAttribute('aria-hidden', 'true');
                
                loanModal.innerHTML = `
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content" id="loan-details-modal-content">
                        </div>
                    </div>
                `;
                
                document.body.appendChild(loanModal);
            }
            
            // Set the modal content and show it
            const modalContentElem = document.getElementById('loan-details-modal-content');
            modalContentElem.innerHTML = modalContent;
            
            // Initialize the modal
            const bsModal = new bootstrap.Modal(loanModal);
            bsModal.show();
        } else {
            console.error('Failed to get loan details:', data.error);
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error(`Error fetching loan details for loan #${loanId}:`, error);
        alert('Failed to fetch loan details: ' + error.message);
    });
}

function extendLoan(loanId) {
    const additionalRounds = prompt(`How many additional rounds to extend loan #${loanId}?`, "3");
    if (additionalRounds !== null) {
        console.log(`Extending loan #${loanId} by ${additionalRounds} rounds`);
        
        fetch(`/api/admin/finance/loans/${loanId}/extend`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Admin-Key': window.adminKey
            },
            body: JSON.stringify({
                additional_rounds: parseInt(additionalRounds)
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert(`Loan #${loanId} has been extended by ${additionalRounds} rounds`);
                refreshLoans();
            } else {
                console.error('Failed to extend loan:', data.error);
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error(`Error extending loan #${loanId}:`, error);
            alert(`Failed to extend loan: ${error.message}`);
            refreshLoans();
        });
    }
}

function payoffLoan(loanId) {
    if (confirm(`Are you sure you want to mark loan #${loanId} as paid off?`)) {
        console.log(`Marking loan #${loanId} as paid off`);
        
        fetch(`/api/admin/finance/loans/${loanId}/payoff`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Admin-Key': window.adminKey
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert(`Loan #${loanId} has been marked as paid off`);
                refreshLoans();
            } else {
                console.error('Failed to pay off loan:', data.error);
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error(`Error paying off loan #${loanId}:`, error);
            alert(`Failed to pay off loan: ${error.message}`);
            refreshLoans();
        });
    }
}

// Function to withdraw a CD
function withdrawCD(cdId) {
    if (confirm(`Are you sure you want to withdraw CD #${cdId}?`)) {
        console.log(`Withdrawing CD #${cdId}`);
        
        fetch(`/api/admin/finance/loans/${cdId}/withdraw`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Admin-Key': window.adminKey
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert(`CD #${cdId} has been withdrawn successfully`);
                refreshLoans();
            } else {
                console.error('Failed to withdraw CD:', data.error);
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error(`Error withdrawing CD #${cdId}:`, error);
            alert(`Failed to withdraw CD: ${error.message}`);
            refreshLoans();
        });
    }
}

// Helper function to format dates nicely
function formatDate(isoString) {
    try {
        const date = new Date(isoString);
        return date.toLocaleString();
    } catch (e) {
        console.error('Error formatting date:', e);
        return isoString; // Return the original string if parsing fails
    }
}

// Add a function to refresh all financial panels independently
function refreshAllFinancialPanels() {
    console.log('Refreshing all financial panels...');
    refreshFinancialOverview();
    refreshLoans();
    refreshTransactions();
}

// Update document.ready to use the new function
$(document).ready(function() {
    // Initial load of financial data
    refreshAllFinancialPanels();
    
    // Set up refresh buttons
    $('#refresh-finance-btn').click(function() {
        refreshAllFinancialPanels();
    });
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeFinanceTab
    };
} 