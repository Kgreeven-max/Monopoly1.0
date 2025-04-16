import logging
import os
import json
import requests
import subprocess
from flask import current_app
from datetime import datetime

class RemoteController:
    """Controller for managing remote connectivity via Cloudflare Tunnel"""
    
    def __init__(self, app=None):
        self.app = app
        self.logger = logging.getLogger(__name__)
        self.tunnel_config_path = os.path.join(os.getcwd(), 'cloudflared_config.json')
        self.tunnel_process = None
        self.tunnel_connected = False
        self.tunnel_url = None
        self.cloudflared_path = self._find_cloudflared_binary()
        
    def _find_cloudflared_binary(self):
        """Find the cloudflared binary in the system path"""
        # First, try the PATH environment variable
        try:
            cloudflared_path = subprocess.check_output(['which', 'cloudflared']).decode('utf-8').strip()
            if cloudflared_path:
                return cloudflared_path
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.logger.warning("cloudflared not found in PATH")
        
        # Check common installation directories
        common_paths = [
            '/usr/local/bin/cloudflared',
            '/usr/bin/cloudflared',
            '/snap/bin/cloudflared',
            os.path.expanduser('~/cloudflared'),
            os.path.join(os.getcwd(), 'cloudflared')
        ]
        
        for path in common_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        
        self.logger.error("cloudflared binary not found. Please install it first.")
        return None
    
    def check_cloudflared_installed(self):
        """Check if cloudflared is installed"""
        return self.cloudflared_path is not None
    
    def get_cloudflared_version(self):
        """Get the cloudflared version"""
        if not self.check_cloudflared_installed():
            return None
        
        try:
            version_output = subprocess.check_output([self.cloudflared_path, 'version']).decode('utf-8').strip()
            return version_output
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error getting cloudflared version: {str(e)}")
            return None
    
    def check_tunnel_config(self):
        """Check if tunnel configuration exists"""
        return os.path.isfile(self.tunnel_config_path)
    
    def load_tunnel_config(self):
        """Load tunnel configuration from file"""
        if not self.check_tunnel_config():
            return None
        
        try:
            with open(self.tunnel_config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.logger.error(f"Error loading tunnel config: {str(e)}")
            return None
    
    def save_tunnel_config(self, config):
        """Save tunnel configuration to file"""
        try:
            with open(self.tunnel_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving tunnel config: {str(e)}")
            return False
    
    def create_tunnel(self, tunnel_name="pinopoly"):
        """Create a new Cloudflare Tunnel"""
        if not self.check_cloudflared_installed():
            return {
                "success": False,
                "message": "cloudflared not installed",
                "tunnel_id": None
            }
        
        # Check if tunnel already exists
        if self.check_tunnel_config():
            config = self.load_tunnel_config()
            if config:
                return {
                    "success": True,
                    "message": "Tunnel already exists",
                    "tunnel_id": config.get("tunnel_id"),
                    "tunnel_name": config.get("tunnel_name")
                }
        
        try:
            # Create new tunnel
            output = subprocess.check_output(
                [self.cloudflared_path, 'tunnel', 'create', tunnel_name],
                stderr=subprocess.STDOUT
            ).decode('utf-8')
            
            # Extract tunnel ID from output (format: "Created tunnel <tunnel_name> with id <tunnel_id>")
            import re
            match = re.search(r'with id ([a-f0-9-]+)', output)
            if not match:
                self.logger.error(f"Failed to extract tunnel ID from output: {output}")
                return {
                    "success": False,
                    "message": "Failed to extract tunnel ID",
                    "tunnel_id": None
                }
                
            tunnel_id = match.group(1)
                
            # Save tunnel config
            config = {
                "tunnel_id": tunnel_id,
                "tunnel_name": tunnel_name,
                "ingress_rules": [
                    {
                        "hostname": f"{tunnel_name}.tunnel.your-subdomain.com",
                        "service": f"http://localhost:{current_app.config.get('PORT', 5000)}"
                    },
                    {
                        "service": "http_status:404"
                    }
                ]
            }
            
            self.save_tunnel_config(config)
            
            return {
                "success": True,
                "message": f"Tunnel {tunnel_name} created successfully",
                "tunnel_id": tunnel_id,
                "tunnel_name": tunnel_name
            }
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error creating tunnel: {e.output.decode('utf-8')}")
            return {
                "success": False,
                "message": f"Error creating tunnel: {e.output.decode('utf-8')}",
                "tunnel_id": None
            }
    
    def start_tunnel(self):
        """Start the Cloudflare Tunnel in the background"""
        if not self.check_cloudflared_installed():
            return {
                "success": False,
                "message": "cloudflared not installed"
            }
        
        if not self.check_tunnel_config():
            return {
                "success": False,
                "message": "Tunnel config not found. Create a tunnel first."
            }
        
        if self.tunnel_process and self.tunnel_process.poll() is None:
            return {
                "success": True,
                "message": "Tunnel is already running",
                "tunnel_url": self.tunnel_url
            }
        
        config = self.load_tunnel_config()
        if not config:
            return {
                "success": False,
                "message": "Failed to load tunnel config"
            }
        
        try:
            # Start tunnel in background
            self.tunnel_process = subprocess.Popen(
                [self.cloudflared_path, 'tunnel', '--config', self.tunnel_config_path, 'run'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a bit for the tunnel to establish
            import time
            time.sleep(3)
            
            # Check if process is still running
            if self.tunnel_process.poll() is not None:
                stderr = self.tunnel_process.stderr.read().decode('utf-8')
                self.logger.error(f"Tunnel process failed to start: {stderr}")
                return {
                    "success": False,
                    "message": f"Tunnel process failed to start: {stderr}"
                }
            
            # Set tunnel connected state
            self.tunnel_connected = True
            self.tunnel_url = f"https://{config['tunnel_name']}.tunnel.your-subdomain.com"
            
            return {
                "success": True,
                "message": "Tunnel started successfully",
                "tunnel_url": self.tunnel_url
            }
            
        except Exception as e:
            self.logger.error(f"Error starting tunnel: {str(e)}")
            return {
                "success": False,
                "message": f"Error starting tunnel: {str(e)}"
            }
    
    def stop_tunnel(self):
        """Stop the Cloudflare Tunnel"""
        if not self.tunnel_process:
            return {
                "success": True,
                "message": "Tunnel is not running"
            }
        
        try:
            # Check if process is still running
            if self.tunnel_process.poll() is None:
                self.tunnel_process.terminate()
                # Wait for process to terminate
                import time
                time.sleep(2)
                
                # Force kill if still running
                if self.tunnel_process.poll() is None:
                    self.tunnel_process.kill()
            
            self.tunnel_connected = False
            self.tunnel_url = None
            
            return {
                "success": True,
                "message": "Tunnel stopped successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error stopping tunnel: {str(e)}")
            return {
                "success": False,
                "message": f"Error stopping tunnel: {str(e)}"
            }
    
    def get_tunnel_status(self):
        """Get the status of the Cloudflare Tunnel"""
        if not self.check_cloudflared_installed():
            return {
                "installed": False,
                "running": False,
                "url": None,
                "message": "cloudflared not installed"
            }
        
        if not self.check_tunnel_config():
            return {
                "installed": True,
                "running": False,
                "url": None,
                "message": "Tunnel not configured"
            }
        
        config = self.load_tunnel_config()
        tunnel_running = self.tunnel_process and self.tunnel_process.poll() is None
        
        return {
            "installed": True,
            "configured": bool(config),
            "running": tunnel_running,
            "url": self.tunnel_url if tunnel_running else None,
            "tunnel_id": config.get("tunnel_id") if config else None,
            "tunnel_name": config.get("tunnel_name") if config else None
        }
    
    def delete_tunnel(self):
        """Delete the Cloudflare Tunnel"""
        if not self.check_cloudflared_installed():
            return {
                "success": False,
                "message": "cloudflared not installed"
            }
        
        if not self.check_tunnel_config():
            return {
                "success": False,
                "message": "Tunnel config not found"
            }
        
        # Stop tunnel if running
        if self.tunnel_process and self.tunnel_process.poll() is None:
            stop_result = self.stop_tunnel()
            if not stop_result["success"]:
                return stop_result
        
        config = self.load_tunnel_config()
        if not config or not config.get("tunnel_id"):
            return {
                "success": False,
                "message": "Invalid tunnel configuration"
            }
        
        try:
            # Delete tunnel
            subprocess.check_output(
                [self.cloudflared_path, 'tunnel', 'delete', config["tunnel_id"]],
                stderr=subprocess.STDOUT
            )
            
            # Remove config file
            if os.path.exists(self.tunnel_config_path):
                os.remove(self.tunnel_config_path)
            
            self.tunnel_connected = False
            self.tunnel_url = None
            
            return {
                "success": True,
                "message": f"Tunnel {config.get('tunnel_name')} deleted successfully"
            }
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error deleting tunnel: {e.output.decode('utf-8')}")
            return {
                "success": False,
                "message": f"Error deleting tunnel: {e.output.decode('utf-8')}"
            }

    def get_connected_players(self):
        """Get a list of all remotely connected players"""
        from src.controllers.socket_controller import connected_players
        
        remote_players = {}
        for player_id, info in connected_players.items():
            if info.get('remote', False):
                # Get disconnection duration if applicable
                disconnect_duration = None
                if not info.get('connected', False) and 'last_disconnect' in info:
                    disconnect_duration = (datetime.now() - info['last_disconnect']).total_seconds()
                
                remote_players[player_id] = {
                    'id': player_id,
                    'username': info.get('username', 'Unknown'),
                    'display_name': info.get('display_name', info.get('username', 'Unknown')),
                    'connected': info.get('connected', False),
                    'last_connect': info.get('last_connect', None),
                    'last_disconnect': info.get('last_disconnect', None),
                    'disconnect_duration': disconnect_duration,
                    'device_info': info.get('device_info', 'Unknown')
                }
        
        return remote_players 