#!/bin/bash
# setup_config.sh - Configuration setup script for Pi-nopoly
# This script helps set up the configuration files for the Pi-nopoly application.

# Ensure we're in the project root directory
if [ ! -d "src" ] || [ ! -d "config" ]; then
    echo "Error: This script must be run from the project root directory."
    exit 1
fi

# Set up color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Pi-nopoly Configuration Setup${NC}"
echo "==============================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required to run this script.${NC}"
    exit 1
fi

# Ensure generate_config.py exists
if [ ! -f "generate_config.py" ]; then
    echo -e "${RED}Error: generate_config.py not found. Please make sure you have the latest version of the Pi-nopoly repository.${NC}"
    exit 1
fi

# Create configuration directory
echo -e "${YELLOW}Setting up configuration directory...${NC}"
mkdir -p config

# Generate base configuration
echo -e "${YELLOW}Generating base configuration...${NC}"
python3 generate_config.py generate --env=base

# Ask which environment configurations to generate
echo ""
echo "Which environment configurations would you like to generate?"
echo "1. Development only"
echo "2. Testing only"
echo "3. Production only"
echo "4. All environments (Development, Testing, Production)"
echo "5. Skip environment configurations"
read -p "Please select an option (1-5): " env_option

case $env_option in
    1)
        echo -e "${YELLOW}Generating development configuration...${NC}"
        python3 generate_config.py generate --env=development
        ;;
    2)
        echo -e "${YELLOW}Generating testing configuration...${NC}"
        python3 generate_config.py generate --env=testing
        ;;
    3)
        echo -e "${YELLOW}Generating production configuration...${NC}"
        python3 generate_config.py generate --env=production
        ;;
    4)
        echo -e "${YELLOW}Generating all environment configurations...${NC}"
        python3 generate_config.py generate --env=development
        python3 generate_config.py generate --env=testing
        python3 generate_config.py generate --env=production
        ;;
    5)
        echo -e "${YELLOW}Skipping environment configurations.${NC}"
        ;;
    *)
        echo -e "${RED}Invalid option. Skipping environment configurations.${NC}"
        ;;
esac

# Check configurations
echo ""
echo -e "${YELLOW}Checking configurations...${NC}"
python3 generate_config.py check

# List available configuration options
echo ""
echo -e "${YELLOW}Available configuration options:${NC}"
python3 generate_config.py list

echo ""
echo -e "${GREEN}Configuration setup complete!${NC}"
echo "You can now edit the configuration files in the config directory to customize your Pi-nopoly installation."
echo "For more information, see the config/README.md file."
echo ""
echo "To override configuration using environment variables, use the format:"
echo "export PINOPOLY_<OPTION_NAME>=<value>"
echo ""
echo "For example:"
echo "export PINOPOLY_DEBUG=true"
echo "export PINOPOLY_PORT=8080"
echo ""
echo "Happy gaming!" 