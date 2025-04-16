# Pi-nopoly Remote Play Feature

This document provides information about the Remote Play feature in Pi-nopoly, which allows players to connect to the game using any device with a web browser.

## Overview

Remote Play enables players to join a Pi-nopoly game from any device with a web browser by connecting through a secure Cloudflare Tunnel. This allows for:

- Play from smartphones, tablets, or computers that are not directly connected to the Pi-nopoly server
- Participation from anywhere with an internet connection
- Seamless reconnection if a player temporarily loses their connection

## Setup Requirements

To enable Remote Play, you need:

1. The Pi-nopoly server running on a device (Raspberry Pi or other computer)
2. Cloudflared binary installed on that device
3. Remote Play enabled in the Pi-nopoly configuration

### Installation

1. First, ensure you have cloudflared installed:
   
   ```bash
   # For Raspberry Pi (ARM):
   curl -L --output cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm
   chmod +x cloudflared
   sudo mv cloudflared /usr/local/bin/
   
   # For Linux x86_64:
   curl -L --output cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
   chmod +x cloudflared
   sudo mv cloudflared /usr/local/bin/
   ```

2. Enable Remote Play in your Pi-nopoly configuration by setting the environment variable:
   
   ```bash
   # Add to your .env file or environment:
   REMOTE_PLAY_ENABLED=true
   REMOTE_PLAY_TIMEOUT=60  # Seconds to wait for reconnection (10-300)
   ```

## Administration

### Enabling Remote Play

1. Log in to the Pi-nopoly Admin interface
2. Navigate to the "Remote Play" tab
3. If this is the first time, click "Create Tunnel" with a suitable name
4. Click "Start Tunnel" to enable remote connectivity

### Managing Remote Play

From the Remote Play administration tab, you can:

- Start and stop the tunnel
- Monitor connected remote players
- Adjust the reconnection timeout
- Ping players to check connection quality
- Remove disconnected players
- Share connection details via QR code

### Troubleshooting

If you encounter issues with Remote Play:

1. Check if cloudflared is installed correctly (`cloudflared version` in terminal)
2. Verify that the tunnel is running in the admin interface
3. Test the connection by pinging active players
4. Check logs for any errors (`pinopoly.log`)

## Player Connection

Players can connect to the game by:

1. Accessing the connection URL or scanning the QR code from the admin panel
2. Entering their player PIN (the 4-digit code assigned when they joined the game)
3. Optionally entering a display name
4. Clicking "Connect to Game"

## Connection Maintenance

- The system automatically pings players every 30 seconds to monitor connection health
- If a player disconnects, they have a configurable time window to reconnect before being removed from the game
- The reconnection process is automatic if a player's device regains connectivity

## Security Considerations

- All connections are secured through Cloudflare Tunnel encryption
- Player authentication is handled via PIN verification
- The admin interface requires admin key authentication for all Remote Play management functions

## API Endpoints

The Remote Play feature exposes several API endpoints:

- `/api/remote/status` - Get tunnel status
- `/api/remote/check-installation` - Check cloudflared installation
- `/api/remote/create` - Create a new tunnel
- `/api/remote/start` - Start the tunnel
- `/api/remote/stop` - Stop the tunnel
- `/api/remote/delete` - Delete the tunnel
- `/api/remote/info` - Get public tunnel information
- `/api/remote/players` - Get connected players
- `/api/remote/players/ping/:id` - Ping a specific player
- `/api/remote/players/remove/:id` - Remove a player
- `/api/remote/timeout` - Update reconnection timeout

## Socket Events

Remote Play uses Socket.IO for real-time communication:

- `connect` - Connection established
- `disconnect` - Connection lost
- `ping`/`pong` - Connection latency testing
- `player_status` - Player status updates
- `reconnect_settings` - Reconnection timeout configuration
- `auth_error` - Authentication failure notification 