#!/bin/bash

# Telegram to Spotify Bot - Setup Script
# This script helps you set up and deploy the bot

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Telegram to Spotify Bot Setup ===${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}No .env file found. Creating from template...${NC}"
    cat > .env << 'EOF'
# Telegram Configuration
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN

# Spotify Configuration
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
SPOTIFY_PLAYLIST_ID=your_playlist_id
SPOTIFY_USERNAME=your_spotify_username

# Chat Control
ALLOWED_CHAT_IDS=-1001234567890

# Bot Behavior
ENABLE_CONFIRMATION_MESSAGES=False
ENABLE_ERROR_MESSAGES=True

# Webhook Settings
WEBHOOK_URL=https://your-domain.com/webhook
APP_HOST=0.0.0.0
APP_PORT=8000
EOF
    echo -e "${GREEN}Created .env file. Please edit it with your credentials.${NC}"
    echo -e "${YELLOW}Run this script again after configuring .env${NC}"
    exit 0
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Determine compose command
if command -v docker compose &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo -e "${GREEN}Docker and Docker Compose found!${NC}"
echo ""

# Function to check if .env is configured
check_env_configured() {
    if grep -q "YOUR_TELEGRAM_BOT_TOKEN" .env || grep -q "your_spotify_client_id" .env; then
        echo -e "${RED}Please configure your .env file with actual values!${NC}"
        echo "Edit .env and replace placeholder values with your actual credentials."
        exit 1
    fi
}

# Menu
echo "What would you like to do?"
echo "1) Setup Spotify authentication"
echo "2) Build Docker image"
echo "3) Start the bot (Docker Compose)"
echo "4) Stop the bot"
echo "5) View logs"
echo "6) Restart the bot"
echo "7) Run locally (without Docker)"
echo "8) Exit"
echo ""
read -p "Enter your choice [1-8]: " choice

case $choice in
    1)
        echo -e "${GREEN}Setting up Spotify authentication...${NC}"
        check_env_configured

        # Install dependencies if needed
        if ! python3 -c "import spotipy" 2>/dev/null; then
            echo "Installing Python dependencies..."
            pip3 install -r requirements.txt
        fi

        echo "This will open a browser for Spotify authentication..."
        python3 -c "from main import sp; print('User:', sp.current_user()['display_name']); print('✓ Authentication successful!')"
        echo -e "${GREEN}Spotify authentication complete!${NC}"
        ;;

    2)
        echo -e "${GREEN}Building Docker image...${NC}"
        $COMPOSE_CMD build
        echo -e "${GREEN}Docker image built successfully!${NC}"
        ;;

    3)
        echo -e "${GREEN}Starting the bot with Docker Compose...${NC}"
        check_env_configured

        # Create cache directory if it doesn't exist
        mkdir -p cache

        # Check if cache file exists
        CACHE_FILE=".cache-$(grep SPOTIFY_USERNAME .env | cut -d '=' -f2)"
        if [ -f "$CACHE_FILE" ]; then
            echo "Copying Spotify authentication cache..."
            cp "$CACHE_FILE" cache/
        else
            echo -e "${YELLOW}Warning: No Spotify authentication cache found.${NC}"
            echo "You may need to authenticate first (option 1)"
            read -p "Continue anyway? (y/n): " continue_choice
            if [ "$continue_choice" != "y" ]; then
                exit 0
            fi
        fi

        $COMPOSE_CMD up -d
        echo -e "${GREEN}Bot started!${NC}"
        echo "View logs with: $COMPOSE_CMD logs -f"
        echo "Or run option 5 from this menu"
        ;;

    4)
        echo -e "${YELLOW}Stopping the bot...${NC}"
        $COMPOSE_CMD down
        echo -e "${GREEN}Bot stopped!${NC}"
        ;;

    5)
        echo -e "${GREEN}Viewing logs (Ctrl+C to exit)...${NC}"
        $COMPOSE_CMD logs -f
        ;;

    6)
        echo -e "${YELLOW}Restarting the bot...${NC}"
        $COMPOSE_CMD restart
        echo -e "${GREEN}Bot restarted!${NC}"
        ;;

    7)
        echo -e "${GREEN}Running locally without Docker...${NC}"
        check_env_configured

        # Install dependencies
        if ! python3 -c "import telegram" 2>/dev/null; then
            echo "Installing Python dependencies..."
            pip3 install -r requirements.txt
        fi

        echo "Starting bot..."
        echo "Press Ctrl+C to stop"
        python3 main.py
        ;;

    8)
        echo "Goodbye!"
        exit 0
        ;;

    *)
        echo -e "${RED}Invalid choice!${NC}"
        exit 1
        ;;
esac
