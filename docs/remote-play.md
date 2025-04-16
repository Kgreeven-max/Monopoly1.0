# Remote Play Feature Documentation

## Overview

Pi-nopoly's Remote Play feature allows players to access and play the game from anywhere with an internet connection, using Cloudflare Tunnel technology for secure, easy-to-set-up remote connectivity.

## Key Features

### Cloudflare Tunnel Integration

- **Zero-Trust Security Model**: No inbound ports opened on your Raspberry Pi
- **Global Network Access**: Connect via Cloudflare's global edge network
- **Custom URL**: Unique subdomain for your game server
- **End-to-End Encryption**: All traffic is encrypted with TLS
- **No Port Forwarding Required**: Works behind NAT/firewalls with no configuration

### Connection Management

- **Automatic Disconnect Detection**: System detects when players lose connection
- **Reconnection Handling**: Players can resume gameplay after disconnection
- **Turn Timeout Mechanism**: Prevents stalled games due to disconnected players
- **Connection Quality Monitoring**: Ping tools to check player connection status
- **QR Code Sharing**: Easy sharing of connection details via QR codes

### Player Management

- **Admin Connection Dashboard**: View all connected players and their status
- **Player Ping Tool**: Measure connection quality for specific players
- **Player Removal Control**: Remove disconnected or inactive players
- **Timeout Settings**: Configure how long to wait for reconnection

## Setup Instructions

### Prerequisites

1. **Cloudflared Installation**

   The Remote Play system requires the Cloudflared client to be installed on your Raspberry Pi.

   ```bash
   # On Raspberry Pi / Debian / Ubuntu
   curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
   sudo dpkg -i cloudflared.deb
   
   # Verify installation
   cloudflared version
   ```

2. **Environment Configuration**

   Ensure the following environment variables are set in your `.env` file:

   ```
   REMOTE_PLAY_ENABLED=true
   REMOTE_PLAY_TIMEOUT=60  # Timeout in seconds
   PORT=5000  # The port your app runs on
   ```

### Creating a Tunnel

1. Access the Admin Panel at `/admin` and log in with your admin key
2. Navigate to the Remote Play section
3. Click "Create Tunnel" and provide a name for your tunnel (e.g., "pinopoly")
4. Wait for the tunnel creation to complete

### Starting the Tunnel

1. In the Admin Panel's Remote Play section, click "Start Tunnel"
2. The system will establish a connection to Cloudflare's network
3. Once connected, a public URL will be displayed

### Sharing Connection Details

1. Navigate to `/connect` to view the connection information
2. Share the displayed URL or QR code with remote players
3. Players can access the game by visiting the URL in a web browser

## Administration

### Monitoring Connections

The Admin Panel provides a real-time view of all connected players with information such as:

- Connection status (connected/disconnected)
- Connection time
- Disconnection duration (if applicable)
- Device information
- Last activity timestamp

### Managing Players

Administrators can:

- **Ping Players**: Test connection quality to individual players
- **Remove Players**: Force-remove disconnected or problematic players
- **Set Timeout Duration**: Configure how long to wait for player reconnection
- **Monitor Turn Status**: See current player turn and timeout countdown

### Tunnel Management

Administrators can:

- **Start/Stop Tunnel**: Control when the tunnel is active
- **Delete Tunnel**: Remove the tunnel configuration when no longer needed
- **View Tunnel Status**: Check if the tunnel is running and accessible

## Technical Details

### Cloudflare Tunnel Architecture

Pi-nopoly uses Cloudflare's Argo Tunnel technology (now called Cloudflare Tunnel) to establish an outbound connection from your Raspberry Pi to Cloudflare's edge network. This creates a secure pathway for traffic to flow between remote players and your game server without exposing ports on your network.

```
Remote Player → Cloudflare Edge Network → Cloudflare Tunnel → Pi-nopoly Server
```

### Reconnection Protocol

When a player disconnects:

1. The system detects the disconnection and marks the player as "disconnected"
2. A reconnection timer starts based on the configured timeout
3. If the player reconnects before the timeout, gameplay continues normally
4. If the timeout is reached, the system:
   - Auto-ends the player's turn (if it was their turn)
   - Notifies all players of the timeout
   - Maintains the player's game state for potential later reconnection

### Security Considerations

- All tunnel traffic is encrypted end-to-end
- No inbound ports are opened on your network
- PIN-based player authentication prevents unauthorized access
- Admin-only controls for tunnel management
- Rate limiting protects against abuse

## Troubleshooting

### Common Issues

1. **Tunnel Creation Fails**
   - Ensure cloudflared is properly installed
   - Check internet connectivity
   - Verify you have permissions to create tunnels

2. **Connection Drops**
   - Check your Raspberry Pi's internet connection
   - Ensure the Pi has sufficient resources available
   - Restart the tunnel or the application

3. **High Latency**
   - Use the ping feature to check connection quality
   - Verify your internet connection speed
   - Consider adjusting the timeout duration for your network conditions

4. **Device Compatibility**
   - Pi-nopoly remote play works best on modern browsers
   - Ensure devices have JavaScript enabled
   - Test on different devices to isolate issues

### Logs and Debugging

- Check `pinopoly.log` for detailed connection logs
- Cloudflared logs can be found using `journalctl -u cloudflared` if installed as a service
- Enable debug mode for more verbose logging

## Best Practices

1. **Network Reliability**
   - Use a wired connection for your Raspberry Pi when possible
   - Ensure stable internet connection for best experience
   - Consider a UPS for your Pi to prevent unexpected shutdowns

2. **Player Experience**
   - Set appropriate timeout values based on your players' connection quality
   - Use the board display on a TV for in-person spectators
   - Recommend players use stable internet connections

3. **Security**
   - Change admin and display keys from defaults
   - Regularly update cloudflared to the latest version
   - Monitor connection logs for unusual activity

## Future Enhancements

Planned improvements for the Remote Play feature:

1. **Enhanced Latency Compensation**
   - Adaptive timeout based on connection quality
   - Predictive movement for smoother experience

2. **Expanded Spectator Mode**
   - Multiple spectator views
   - Spectator chat
   - Game replay features

3. **Additional Security Features**
   - Two-factor authentication for admin access
   - Enhanced audit logging
   - Custom access controls 