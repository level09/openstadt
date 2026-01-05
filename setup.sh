#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}OpenStadt Setup${NC}"
echo "=================="
echo

# Check for uv
if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: uv is not installed.${NC}"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
uv sync --extra dev

# Create .env if not exists
if [ ! -f .env ]; then
    echo -e "${GREEN}Creating .env from template...${NC}"
    cp .env-sample .env

    # Generate secure keys
    SECRET_KEY=$(openssl rand -base64 32 | tr -dc 'A-Za-z0-9' | head -c 32)
    SALT=$(openssl rand -base64 32 | tr -dc 'A-Za-z0-9' | head -c 32)
    TOTP=$(openssl rand -base64 32 | tr -dc 'A-Za-z0-9' | head -c 32)

    # Update .env with secure values
    sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=\"$SECRET_KEY\"/" .env 2>/dev/null || \
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=\"$SECRET_KEY\"/" .env

    sed -i '' "s/SECURITY_PASSWORD_SALT=.*/SECURITY_PASSWORD_SALT=\"$SALT\"/" .env 2>/dev/null || \
    sed -i "s/SECURITY_PASSWORD_SALT=.*/SECURITY_PASSWORD_SALT=\"$SALT\"/" .env

    sed -i '' "s/SECURITY_TOTP_SECRETS=.*/SECURITY_TOTP_SECRETS=\"$TOTP\"/" .env 2>/dev/null || \
    sed -i "s/SECURITY_TOTP_SECRETS=.*/SECURITY_TOTP_SECRETS=\"$TOTP\"/" .env

    echo -e "${GREEN}Generated secure keys in .env${NC}"
else
    echo -e "${YELLOW}.env already exists, skipping...${NC}"
fi

# Create instance directory
mkdir -p instance

echo
echo -e "${GREEN}Setup complete!${NC}"
echo
echo "Next steps:"
echo -e "  1. ${GREEN}uv run flask create-db${NC}       # Create database tables"
echo -e "  2. ${GREEN}uv run flask install${NC}         # Create admin user"
echo -e "  3. ${GREEN}uv run flask load-city config/cities/mannheim.yaml${NC}"
echo -e "  4. ${GREEN}uv run flask run${NC}             # Start server at http://localhost:5000"
echo
echo "For OSM data sync:"
echo -e "  ${GREEN}uv run flask sync-osm mannheim playgrounds${NC}"
echo
