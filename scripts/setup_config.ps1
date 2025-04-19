# setup_config.ps1 - Configuration setup script for Pi-nopoly (Windows)
# This script helps set up the configuration files for the Pi-nopoly application on Windows systems.

# Function to display colored output
function Write-ColorOutput {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [string]$ForegroundColor = "White"
    )
    
    $originalColor = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    Write-Output $Message
    $host.UI.RawUI.ForegroundColor = $originalColor
}

# Ensure we're in the project root directory
if (-not ((Test-Path "src") -and (Test-Path "config"))) {
    Write-ColorOutput "Error: This script must be run from the project root directory." "Red"
    exit 1
}

Write-ColorOutput "Pi-nopoly Configuration Setup" "Green"
Write-Output "==============================="
Write-Output ""

# Check if Python is installed
try {
    $pythonVersion = python --version
    if (-not $pythonVersion) {
        throw "Python not found"
    }
} catch {
    Write-ColorOutput "Error: Python is required to run this script." "Red"
    Write-ColorOutput "Please install Python and ensure it's in your PATH." "Red"
    exit 1
}

# Ensure generate_config.py exists
if (-not (Test-Path "generate_config.py")) {
    Write-ColorOutput "Error: generate_config.py not found. Please make sure you have the latest version of the Pi-nopoly repository." "Red"
    exit 1
}

# Create configuration directory
Write-ColorOutput "Setting up configuration directory..." "Yellow"
if (-not (Test-Path "config")) {
    New-Item -Path "config" -ItemType Directory | Out-Null
}

# Generate base configuration
Write-ColorOutput "Generating base configuration..." "Yellow"
python generate_config.py generate --env=base

# Ask which environment configurations to generate
Write-Output ""
Write-Output "Which environment configurations would you like to generate?"
Write-Output "1. Development only"
Write-Output "2. Testing only"
Write-Output "3. Production only"
Write-Output "4. All environments (Development, Testing, Production)"
Write-Output "5. Skip environment configurations"
$envOption = Read-Host "Please select an option (1-5)"

switch ($envOption) {
    "1" {
        Write-ColorOutput "Generating development configuration..." "Yellow"
        python generate_config.py generate --env=development
    }
    "2" {
        Write-ColorOutput "Generating testing configuration..." "Yellow"
        python generate_config.py generate --env=testing
    }
    "3" {
        Write-ColorOutput "Generating production configuration..." "Yellow"
        python generate_config.py generate --env=production
    }
    "4" {
        Write-ColorOutput "Generating all environment configurations..." "Yellow"
        python generate_config.py generate --env=development
        python generate_config.py generate --env=testing
        python generate_config.py generate --env=production
    }
    "5" {
        Write-ColorOutput "Skipping environment configurations." "Yellow"
    }
    default {
        Write-ColorOutput "Invalid option. Skipping environment configurations." "Red"
    }
}

# Check configurations
Write-Output ""
Write-ColorOutput "Checking configurations..." "Yellow"
python generate_config.py check

# List available configuration options
Write-Output ""
Write-ColorOutput "Available configuration options:" "Yellow"
python generate_config.py list

Write-Output ""
Write-ColorOutput "Configuration setup complete!" "Green"
Write-Output "You can now edit the configuration files in the config directory to customize your Pi-nopoly installation."
Write-Output "For more information, see the config/README.md file."
Write-Output ""
Write-Output "To override configuration using environment variables, use the format:"
Write-Output "For cmd.exe:"
Write-Output "    set PINOPOLY_<OPTION_NAME>=<value>"
Write-Output ""
Write-Output "For PowerShell:"
Write-Output "    `$env:PINOPOLY_<OPTION_NAME> = '<value>'"
Write-Output ""
Write-Output "For example:"
Write-Output "    `$env:PINOPOLY_DEBUG = 'true'"
Write-Output "    `$env:PINOPOLY_PORT = '8080'"
Write-Output ""
Write-Output "Happy gaming!"

# Pause at the end so users can read the output
Write-Output ""
Write-Output "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 