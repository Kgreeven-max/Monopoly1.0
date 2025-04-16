import React, { useState, useEffect } from 'react';
import { useSocket } from '../contexts/SocketContext';
import { usePlayer } from '../contexts/PlayerContext';
import '../styles/AuctionModal.css';

const AuctionModal = ({ auction, onClose }) => {
  const { socket } = useSocket();
  const { player } = usePlayer();
  const [bid, setBid] = useState('');
  const [error, setError] = useState('');
  const [secondsRemaining, setSecondsRemaining] = useState(auction?.timer || 30);
  const [bidHistory, setBidHistory] = useState(auction?.bids || []);
  const [currentBid, setCurrentBid] = useState(auction?.current_bid || 0);
  const [currentBidder, setCurrentBidder] = useState(auction?.current_bidder || null);
  const [isActive, setIsActive] = useState(auction?.status === 'active');

  useEffect(() => {
    if (!socket) return;

    // Listen for timer updates
    const timerListener = (data) => {
      if (data.auction_id === auction.id) {
        setSecondsRemaining(data.seconds_remaining);
      }
    };

    // Listen for new bids
    const bidListener = (data) => {
      if (data.auction_id === auction.id) {
        setCurrentBid(data.bid_amount);
        setCurrentBidder(data.player_id);
        setSecondsRemaining(data.seconds_remaining);
        
        // Add to bid history
        setBidHistory(prev => [
          ...prev,
          { player_id: data.player_id, player_name: data.player_name, amount: data.bid_amount }
        ]);
      }
    };

    // Listen for auction end
    const endListener = (data) => {
      if (data.auction_id === auction.id) {
        setIsActive(false);
      }
    };

    // Listen for errors
    const errorListener = (data) => {
      setError(data.error);
      setTimeout(() => setError(''), 5000);
    };

    // Listen for pass updates
    const passListener = (data) => {
      if (data.auction_id === auction.id) {
        // Add to bid history
        setBidHistory(prev => [
          ...prev,
          { player_id: data.player_id, player_name: data.player_name, action: 'pass' }
        ]);
      }
    };

    socket.on('auction_timer', timerListener);
    socket.on('auction_bid', bidListener);
    socket.on('auction_ended', endListener);
    socket.on('auction_error', errorListener);
    socket.on('auction_pass', passListener);

    return () => {
      socket.off('auction_timer', timerListener);
      socket.off('auction_bid', bidListener);
      socket.off('auction_ended', endListener);
      socket.off('auction_error', errorListener);
      socket.off('auction_pass', passListener);
    };
  }, [socket, auction.id]);

  const handleBidChange = (e) => {
    setBid(e.target.value);
  };

  const placeBid = () => {
    setError('');
    const bidAmount = parseInt(bid);
    
    if (isNaN(bidAmount) || bidAmount <= 0) {
      setError('Please enter a valid bid amount');
      return;
    }

    if (bidAmount <= currentBid) {
      setError(`Bid must be higher than current bid: $${currentBid}`);
      return;
    }

    socket.emit('place_bid', {
      auction_id: auction.id,
      player_id: player.id,
      pin: player.pin,
      bid_amount: bidAmount
    });

    // Clear bid input after submission
    setBid('');
  };

  const passAuction = () => {
    socket.emit('pass_auction', {
      auction_id: auction.id,
      player_id: player.id,
      pin: player.pin
    });
  };

  const getMinimumBid = () => {
    if (currentBid < auction.minimum_bid) {
      return auction.minimum_bid;
    }
    return currentBid + 1;
  };

  const isPlayerCurrentBidder = currentBidder === player.id;
  const hasPlayerPassed = auction.players_passed?.includes(player.id);
  const canBid = isActive && !hasPlayerPassed && !isPlayerCurrentBidder;

  return (
    <div className="auction-modal-backdrop">
      <div className="auction-modal">
        <div className="auction-header">
          <h2>{auction.is_foreclosure ? 'Foreclosure Auction' : 'Property Auction'}</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        <div className="auction-property">
          <h3>{auction.property_name}</h3>
          <div className="property-details">
            <p>List Price: ${auction.start_price}</p>
            <p>Minimum Bid: ${auction.minimum_bid}</p>
            {auction.is_foreclosure && (
              <p className="foreclosure-notice">Foreclosure Sale</p>
            )}
          </div>
        </div>

        <div className="auction-status">
          <div className="timer">
            <span className={secondsRemaining <= 10 ? 'urgent' : ''}>
              Time Remaining: {secondsRemaining} seconds
            </span>
          </div>
          
          <div className="current-bid">
            <h4>Current Bid: ${currentBid >= auction.minimum_bid ? currentBid : 'No bids yet'}</h4>
            {currentBidder && (
              <p>Highest Bidder: {bidHistory.find(b => b.player_id === currentBidder)?.player_name || 'Unknown'}</p>
            )}
          </div>
        </div>

        {isActive && (
          <div className="auction-actions">
            {canBid ? (
              <>
                <div className="bid-controls">
                  <input
                    type="number"
                    min={getMinimumBid()}
                    value={bid}
                    onChange={handleBidChange}
                    placeholder={`Min bid: $${getMinimumBid()}`}
                  />
                  <button onClick={placeBid} className="bid-button">Place Bid</button>
                </div>
                <button onClick={passAuction} className="pass-button">Pass</button>
              </>
            ) : (
              <div className="auction-message">
                {isPlayerCurrentBidder ? (
                  <p className="current-bidder-message">You are the highest bidder!</p>
                ) : hasPlayerPassed ? (
                  <p className="passed-message">You have passed on this auction</p>
                ) : (
                  <p>Waiting for auction to complete...</p>
                )}
              </div>
            )}
          </div>
        )}

        {!isActive && (
          <div className="auction-results">
            <h3>Auction Ended</h3>
            {currentBidder ? (
              <p>Property sold to {bidHistory.find(b => b.player_id === currentBidder)?.player_name} for ${currentBid}</p>
            ) : (
              <p>Property did not sell</p>
            )}
          </div>
        )}

        {error && <div className="error-message">{error}</div>}

        <div className="bid-history">
          <h4>Bid History</h4>
          <div className="bid-list">
            {bidHistory.length > 0 ? (
              <ul>
                {bidHistory.map((bid, index) => (
                  <li key={index}>
                    {bid.action === 'pass' ? (
                      <span>{bid.player_name} passed</span>
                    ) : (
                      <span>{bid.player_name}: ${bid.amount}</span>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="no-bids">No bids yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuctionModal; 