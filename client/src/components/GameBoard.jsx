import MarketCrashDisplay from './MarketCrashDisplay';
import TeamDisplay from './TeamDisplay';

const GameBoard = ({ gameId }) => {
  const [gameMode, setGameMode] = useState(null);

  useEffect(() => {
    const fetchGameMode = async () => {
      try {
        const response = await GameModeService.getGameModeSettings(gameId);
        if (response.success) {
          setGameMode(response.mode);
        }
      } catch (err) {
        console.error('Error fetching game mode:', err);
      }
    };

    fetchGameMode();
  }, [gameId]);

  return (
    <div className="game-board">
      {/* Existing game board content */}
      
      {gameMode === 'market_crash' && (
        <div className="market-crash-panel">
          <MarketCrashDisplay gameId={gameId} />
        </div>
      )}
      
      {gameMode === 'team_battle' && (
        <div className="team-panel">
          <TeamDisplay gameId={gameId} />
        </div>
      )}
      
      {/* Rest of the game board content */}
    </div>
  );
};

export default GameBoard; 