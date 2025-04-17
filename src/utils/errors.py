class GameError(Exception):
    """Custom exception class for game-related errors"""
    
    def __init__(self, message: str):
        """Initialize with error message
        
        Args:
            message: The error message to display
        """
        self.message = message
        super().__init__(self.message)
        
    def __str__(self):
        return self.message 