/**
 * AuctionTimer - Utility class that manages countdown for property auctions
 */
class AuctionTimer {
    /**
     * Creates a new AuctionTimer instance
     * @param {number} duration - Duration in seconds
     * @param {Function} updateCallback - Function to call on each timer update
     * @param {Function} completeCallback - Function to call when timer completes
     */
    constructor(duration, updateCallback, completeCallback) {
        this.duration = duration;
        this.timeRemaining = duration;
        this.updateCallback = updateCallback;
        this.completeCallback = completeCallback;
        this.interval = null;
        this.isRunning = false;
        this.isPaused = false;
    }
    
    /**
     * Starts the timer
     */
    start() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.isPaused = false;
        
        // Call update immediately to show current time
        this._updateTime();
        
        this.interval = setInterval(() => {
            if (this.isPaused) return;
            
            this.timeRemaining--;
            
            if (this.timeRemaining <= 0) {
                this.stop();
                this._complete();
                return;
            }
            
            this._updateTime();
        }, 1000);
    }
    
    /**
     * Stops the timer
     */
    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
        
        this.isRunning = false;
    }
    
    /**
     * Pauses the timer
     */
    pause() {
        this.isPaused = true;
    }
    
    /**
     * Resumes the timer after pause
     */
    resume() {
        this.isPaused = false;
    }
    
    /**
     * Resets the timer to its original duration
     */
    reset() {
        this.timeRemaining = this.duration;
        this._updateTime();
    }
    
    /**
     * Sets a new duration and resets the timer
     * @param {number} seconds - New duration in seconds
     */
    setDuration(seconds) {
        this.duration = seconds;
        this.reset();
    }
    
    /**
     * Gets the remaining time in seconds
     * @returns {number} - Remaining time in seconds
     */
    getTimeRemaining() {
        return this.timeRemaining;
    }
    
    /**
     * Gets formatted time string (MM:SS)
     * @returns {string} - Formatted time string
     */
    getFormattedTime() {
        const minutes = Math.floor(this.timeRemaining / 60);
        const seconds = this.timeRemaining % 60;
        
        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    
    /**
     * Updates the timer display via callback
     * @private
     */
    _updateTime() {
        if (typeof this.updateCallback === 'function') {
            const minutes = Math.floor(this.timeRemaining / 60);
            const seconds = this.timeRemaining % 60;
            
            this.updateCallback(minutes, seconds);
        }
    }
    
    /**
     * Calls the completion callback
     * @private
     */
    _complete() {
        if (typeof this.completeCallback === 'function') {
            this.completeCallback();
        }
    }
} 