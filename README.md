# Pi-nopoly

A modern digital implementation of the classic board game, designed to run on Raspberry Pi or any computer with a web browser.

## Features

- **Digital Game Board**: Interactive digital board that can be displayed on TV screens
- **Player Management**: Support for multiple players, including AI opponents
- **Property Trading**: Full implementation of property purchasing, renting, and trading
- **Special Events**: Random events, community fund, and special spaces
- **Crime System**: Enhanced gameplay with police patrols and criminal activities
- **Adaptive Difficulty**: AI opponents that adapt to player skill levels
- **Game Modes**: Multiple game modes with unique rules and objectives (NEW!)
- **Remote Play**: Connect from any device with a web browser via Cloudflare Tunnel (NEW!)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pinopoly.git
   cd pinopoly
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your environment variables (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

4. Run the game:
   ```bash
   python app.py
   ```

## Game Modes

Pi-nopoly now offers multiple game modes to suit different playstyles:

### Standard Modes
- **Classic Mode**: Traditional gameplay with property acquisition and monopolies
- **Speed Mode**: Faster gameplay with time/turn limits for quicker sessions
- **Co-op Mode**: Players work together to develop properties before economic collapse

### Specialty Modes
- **Tycoon Mode**: Focus on property development with advanced improvement options
- **Market Crash Mode**: Navigate economic turmoil with volatile property values
- **Team Battle Mode**: Team-based competition with shared resources

Each mode features:
- Customizable settings
- Unique win conditions
- Special gameplay mechanics
- Mode-specific achievements

For detailed information, see the [Game Modes documentation](docs/game-modes.md).

## Remote Play

Pi-nopoly now features robust remote play capabilities, allowing players to connect from any device with a web browser through a secure Cloudflare Tunnel. This is perfect for:

- Players who want to use their smartphones as controllers
- Game sessions with participants in different locations
- Large groups where not everyone can see the main screen

To enable Remote Play:

1. Install cloudflared on your server (see [Remote Play documentation](docs/remote_play.md))
2. Set `REMOTE_PLAY_ENABLED=true` in your environment variables
3. Access the admin panel and configure the tunnel
4. Share the connection link or QR code with players

Remote play features include:
- Secure connections through Cloudflare Tunnel
- QR code sharing for easy connection
- Auto-reconnection for dropped connections
- Player status monitoring
- Turn timeout management

For detailed instructions, see the [Remote Play documentation](docs/remote_play.md).

## Game Setup

1. Access the admin interface by navigating to `/admin` in your browser
2. Configure game settings
3. Add players (human or AI)
4. Start the game
5. Display the board on a TV by navigating to `/board`

## Project Structure

- `app.py` - Main application entry point
- `src/` - Source code for game logic and controllers
- `static/` - Static assets (JS, CSS, images)
- `templates/` - HTML templates
- `docs/` - Documentation

## Documentation

- [Game Modes](docs/game-modes.md)
- [Remote Play Setup](docs/remote_play.md)
- [Admin Panel Guide](docs/admin_panel.md)
- [API Reference](docs/api_reference.md)
- [Game Rules](docs/game_rules.md)

## Technologies Used

- **Backend**: Python with Flask
- **Frontend**: React with JavaScript/JSX
- **Real-time Communication**: Socket.IO
- **Remote Connectivity**: Cloudflare Tunnel
- **Database**: SQLite (default) or PostgreSQL

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by the classic board game
- Built for educational and entertainment purposes
- Special thanks to all contributors 