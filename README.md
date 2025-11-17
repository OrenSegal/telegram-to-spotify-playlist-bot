# Telegram to Spotify Playlist Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

A Telegram bot that automatically reads Spotify links from group chats and adds them to a specified Spotify playlist.

## Features

- Automatically detects and processes Spotify links in Telegram group chats
- Supports multiple link types:
  - Individual tracks
  - Full albums (adds all tracks)
  - Playlists (adds all tracks from shared playlists)
- Intelligent duplicate prevention
- Batch processing for efficient API usage
- Configurable notifications (confirmations and errors)
- Docker support for easy deployment
- Webhook-based for reliable message delivery
- Health check endpoint for monitoring
- FastAPI-based web server with proper async handling

## Quick Start

For the fastest setup, use the interactive setup script:

```bash
chmod +x setup.sh
./setup.sh
```

Or use Make commands:

```bash
make install    # Install dependencies
make auth       # Authenticate with Spotify
make up         # Start with Docker Compose
make logs       # View logs
```

For detailed setup instructions, see below.

## Prerequisites

- Python 3.9 or higher
- A Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Spotify Developer Application credentials
- A Spotify playlist ID where tracks will be added
- A publicly accessible URL for webhooks (production deployment)
- Docker (optional, for containerized deployment)

## Setup Instructions

### 1. Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the instructions
3. Save the bot token provided
4. Add your bot to the desired group chat
5. Get the chat ID:
   - Add [@userinfobot](https://t.me/userinfobot) or [@myidbot](https://t.me/myidbot) to your group
   - It will display the chat ID (will be negative for groups, e.g., `-1001234567890`)
   - Remove the bot after getting the ID

### 2. Set Up Spotify API

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click "Create an App"
4. Fill in app name and description
5. Note your **Client ID** and **Client Secret**
6. Click "Edit Settings"
7. Add `http://localhost:8888/callback` to **Redirect URIs** and save
8. Create or find the Spotify playlist where tracks will be added
9. Get the playlist ID from the playlist URL:
   - URL format: `https://open.spotify.com/playlist/PLAYLIST_ID?si=...`
   - The playlist ID is the part between `/playlist/` and `?`

### 3. Configure Environment Variables

Edit the `.env` file with your credentials:

```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Spotify Configuration
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
SPOTIFY_PLAYLIST_ID=your_playlist_id_here
SPOTIFY_USERNAME=your_spotify_username

# Chat Control (comma-separated list of allowed chat IDs)
ALLOWED_CHAT_IDS=-1001234567890,-1009876543210

# Bot Behavior
ENABLE_CONFIRMATION_MESSAGES=False
ENABLE_ERROR_MESSAGES=True

# Webhook Settings (update for production)
WEBHOOK_URL=https://your-domain.com/webhook
APP_HOST=0.0.0.0
APP_PORT=8000
```

**Important:** Do NOT commit your `.env` file to version control!

### 4. Verify Setup (Optional but Recommended)

Run the verification script to check if everything is configured correctly:

```bash
python verify.py
```

This will check:
- Required files exist
- Environment variables are configured
- Dependencies are installed
- Code syntax is valid
- Spotify authentication status

### 5. Install Dependencies

```bash
pip install -r requirements.txt
# or
make install
```

### 6. Authenticate with Spotify

Before running the bot, authenticate with Spotify:

```bash
python -c "from main import sp; print(sp.current_user())"
```

This will:
1. Open a browser window for Spotify OAuth
2. Ask you to authorize the application
3. Redirect to localhost (you'll see an error page, that's OK)
4. Copy the full URL from the browser
5. Paste it back in the terminal

A cache file `.cache-<username>` will be created to store the token.

## Running the Bot

### Local Development (using ngrok)

For local testing with webhooks, you need to expose your local server to the internet using ngrok:

1. Install [ngrok](https://ngrok.com/download)

2. Start ngrok:
   ```bash
   ngrok http 8000
   ```

3. Copy the HTTPS URL (e.g., `https://abcd1234.ngrok.io`)

4. Update `.env`:
   ```env
   WEBHOOK_URL=https://abcd1234.ngrok.io/webhook
   ```

5. Run the bot:
   ```bash
   python main.py
   ```

6. Test by sending a Spotify link in your Telegram group!

### Production Deployment with Docker

1. Build the Docker image:
   ```bash
   docker build -t telegram-spotify-bot .
   ```

2. Run the container:
   ```bash
   docker run -d \
     --name telegram-spotify-bot \
     --env-file .env \
     -p 8000:8000 \
     -v $(pwd)/.cache:/app/.cache \
     telegram-spotify-bot
   ```

3. Check logs:
   ```bash
   docker logs -f telegram-spotify-bot
   ```

### Production Deployment on Heroku

1. Install Heroku CLI and login:
   ```bash
   heroku login
   ```

2. Create a new Heroku app:
   ```bash
   heroku create your-app-name
   ```

3. Set environment variables:
   ```bash
   heroku config:set TELEGRAM_BOT_TOKEN=your_token
   heroku config:set SPOTIFY_CLIENT_ID=your_client_id
   heroku config:set SPOTIFY_CLIENT_SECRET=your_client_secret
   heroku config:set SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
   heroku config:set SPOTIFY_PLAYLIST_ID=your_playlist_id
   heroku config:set SPOTIFY_USERNAME=your_username
   heroku config:set ALLOWED_CHAT_IDS=-1001234567890
   heroku config:set WEBHOOK_URL=https://your-app-name.herokuapp.com/webhook
   heroku config:set ENABLE_CONFIRMATION_MESSAGES=False
   heroku config:set ENABLE_ERROR_MESSAGES=True
   ```

4. Deploy:
   ```bash
   git push heroku main
   ```

5. Check logs:
   ```bash
   heroku logs --tail
   ```

## Configuration Options

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Yes | - |
| `SPOTIFY_CLIENT_ID` | Spotify app client ID | Yes | - |
| `SPOTIFY_CLIENT_SECRET` | Spotify app client secret | Yes | - |
| `SPOTIFY_REDIRECT_URI` | OAuth redirect URI | Yes | - |
| `SPOTIFY_PLAYLIST_ID` | Target playlist ID | Yes | - |
| `SPOTIFY_USERNAME` | Your Spotify username | Yes | - |
| `ALLOWED_CHAT_IDS` | Comma-separated chat IDs | Yes | - |
| `ENABLE_CONFIRMATION_MESSAGES` | Send success messages | No | `False` |
| `ENABLE_ERROR_MESSAGES` | Send error messages | No | `True` |
| `WEBHOOK_URL` | Public webhook URL | Yes | - |
| `APP_HOST` | Server bind address | No | `0.0.0.0` |
| `APP_PORT` | Server port | No | `8000` |

## Usage

Once the bot is running and added to your group:

1. Share any Spotify link in the chat:
   - **Track**: `https://open.spotify.com/track/...` → Adds single track
   - **Album**: `https://open.spotify.com/album/...` → Adds all album tracks
   - **Playlist**: `https://open.spotify.com/playlist/...` → Adds all playlist tracks

2. The bot processes links silently (unless notifications are enabled)

3. Check your target playlist to see the added tracks!

## Bot Commands

- `/start` - Display welcome message and bot capabilities

## API Endpoints

- `POST /webhook` - Telegram webhook endpoint
- `GET /health` - Health check endpoint (returns `{"status": "healthy"}`)

## Troubleshooting

### Bot doesn't respond to messages

- Ensure the bot is added to the group
- Verify the chat ID is in `ALLOWED_CHAT_IDS`
- Check webhook status:
  ```bash
  curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
  ```

### Spotify authentication issues

- Delete the `.cache-<username>` file and re-authenticate
- Verify the redirect URI matches exactly in Spotify dashboard
- Ensure you have proper scopes: `playlist-modify-public playlist-modify-private playlist-read-private`

### Webhook errors

- Ensure `WEBHOOK_URL` is publicly accessible with HTTPS
- Check server logs: `docker logs telegram-spotify-bot`
- Test webhook manually:
  ```bash
  curl -X POST https://your-webhook-url/webhook \
    -H "Content-Type: application/json" \
    -d '{"update_id": 1}'
  ```

### Duplicate tracks being added

- The bot caches playlist contents for performance
- If duplicates occur, restart the bot to refresh the cache

## Architecture

- **FastAPI**: Modern async web framework for webhook handling
- **python-telegram-bot v20+**: Official Telegram Bot API wrapper with async support
- **Spotipy**: Spotify Web API wrapper
- **Pydantic v2**: Data validation and settings management
- **Uvicorn**: High-performance ASGI server

## Project Structure

```
telegram-to-spotify-playlist-bot/
├── main.py                   # Main application code
├── config.py                 # Configuration management
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose setup
├── Makefile                 # Helpful Make commands
├── setup.sh                 # Interactive setup script
├── verify.py                # Configuration verification
├── .env                     # Environment variables (not in git)
├── .env.example             # Environment template
├── .gitignore              # Git ignore rules
├── pyproject.toml          # Project metadata
├── README.md               # This file
├── DEPLOYMENT.md           # Comprehensive deployment guide
└── .github/
    └── workflows/
        ├── ci.yml          # CI/CD workflow
        └── docker-publish.yml  # Docker build and publish
```

## Deployment

For production deployment options (Heroku, Railway, DigitalOcean, AWS, Google Cloud), see the comprehensive [DEPLOYMENT.md](DEPLOYMENT.md) guide.

Quick deployment options:
- **Docker Compose**: `make up` (recommended for VPS)
- **Heroku**: See [DEPLOYMENT.md](DEPLOYMENT.md#heroku)
- **Railway**: See [DEPLOYMENT.md](DEPLOYMENT.md#railwayapp)
- **GitHub Container Registry**: Automatic builds on push to main

## Development

### Helpful Commands

The project includes several tools to make development easier:

```bash
# Setup and verification
./setup.sh          # Interactive setup wizard
python verify.py    # Verify configuration

# Development
make install        # Install dependencies
make auth          # Authenticate with Spotify
make run           # Run locally
make format        # Format code with Black
make lint          # Run linters

# Docker
make build         # Build Docker image
make up            # Start with Docker Compose
make down          # Stop containers
make logs          # View logs
make restart       # Restart containers

# Health and monitoring
make health        # Check bot health
make webhook-info  # Check Telegram webhook status
```

### Code Style

Format code with Black:
```bash
pip install black
black main.py config.py
# or
make format
```

### Adding Features

The `SpotifyLinkProcessor` class in `main.py` handles all Spotify operations. To add support for new link types:

1. Update `SPOTIFY_LINK_REGEX` to match the new pattern
2. Add a processing method in `SpotifyLinkProcessor`
3. Add handling logic in `handle_message()`

## Security Notes

- Never commit `.env` file or Spotify cache files
- Use environment variables for all secrets
- The bot only responds to whitelisted chat IDs
- Webhook endpoint validates all incoming requests
- OAuth tokens are stored securely with proper scopes

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions:
- Open a GitHub issue
- Check existing issues for solutions

## Acknowledgments

- Built with [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- Spotify integration via [Spotipy](https://github.com/plamere/spotipy)
- Web framework by [FastAPI](https://fastapi.tiangolo.com/)
