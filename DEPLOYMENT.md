# Deployment Guide

This guide covers various deployment options for the Telegram to Spotify Bot.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Platforms](#cloud-platforms)
5. [CI/CD with GitHub Actions](#cicd-with-github-actions)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)

## Prerequisites

Before deploying, ensure you have:

- Telegram Bot Token (from @BotFather)
- Spotify Developer credentials (Client ID & Secret)
- Spotify Playlist ID
- Allowed Telegram Chat IDs
- Publicly accessible HTTPS URL for webhooks (production)

## Local Development

### Quick Start with Setup Script

```bash
# Make setup script executable
chmod +x setup.sh

# Run setup script
./setup.sh
```

The script will guide you through:
1. Creating `.env` file
2. Spotify authentication
3. Building and running the bot

### Manual Setup

```bash
# 1. Install dependencies
make install
# or
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 3. Authenticate with Spotify
make auth
# or
python -c "from main import sp; print(sp.current_user())"

# 4. Run with ngrok for local testing
# Terminal 1: Start ngrok
ngrok http 8000

# Update WEBHOOK_URL in .env with ngrok URL
# Terminal 2: Run bot
make run
# or
python main.py
```

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and start
make up
# or
docker compose up -d

# View logs
make logs
# or
docker compose logs -f

# Stop
make down
# or
docker compose down
```

### Using Docker Directly

```bash
# Build image
docker build -t telegram-spotify-bot .

# Run container
docker run -d \
  --name telegram-spotify-bot \
  --env-file .env \
  -p 8000:8000 \
  -v $(pwd)/cache:/app/.cache \
  telegram-spotify-bot

# View logs
docker logs -f telegram-spotify-bot

# Stop
docker stop telegram-spotify-bot
docker rm telegram-spotify-bot
```

## Cloud Platforms

### Heroku

```bash
# 1. Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# 2. Login
heroku login

# 3. Create app
heroku create your-app-name

# 4. Set environment variables
heroku config:set TELEGRAM_BOT_TOKEN=your_token
heroku config:set SPOTIFY_CLIENT_ID=your_client_id
heroku config:set SPOTIFY_CLIENT_SECRET=your_secret
heroku config:set SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
heroku config:set SPOTIFY_PLAYLIST_ID=your_playlist_id
heroku config:set SPOTIFY_USERNAME=your_username
heroku config:set ALLOWED_CHAT_IDS=-1001234567890
heroku config:set WEBHOOK_URL=https://your-app-name.herokuapp.com/webhook
heroku config:set ENABLE_CONFIRMATION_MESSAGES=False
heroku config:set ENABLE_ERROR_MESSAGES=True

# 5. Deploy using Container Registry
heroku container:push web
heroku container:release web

# 6. View logs
heroku logs --tail
```

### Railway.app

```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
railway init

# 4. Add environment variables via Railway dashboard
# Go to your project → Variables → Add all .env variables

# 5. Deploy
railway up

# 6. Get public URL and update WEBHOOK_URL
railway domain
```

### DigitalOcean App Platform

1. Fork/push your repository to GitHub
2. Go to DigitalOcean → Apps → Create App
3. Connect your GitHub repository
4. Configure:
   - **Type**: Web Service
   - **Dockerfile Path**: Dockerfile
   - **HTTP Port**: 8000
5. Add environment variables from `.env`
6. Deploy
7. Get the app URL and update `WEBHOOK_URL`

### AWS Elastic Container Service (ECS)

```bash
# 1. Install AWS CLI
# Follow: https://aws.amazon.com/cli/

# 2. Configure AWS credentials
aws configure

# 3. Build and push to ECR
aws ecr create-repository --repository-name telegram-spotify-bot
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

docker build -t telegram-spotify-bot .
docker tag telegram-spotify-bot:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/telegram-spotify-bot:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/telegram-spotify-bot:latest

# 4. Create ECS task and service (via AWS Console or CLI)
# Set environment variables in task definition
# Configure ALB for HTTPS webhook endpoint
```

### Google Cloud Run

```bash
# 1. Install gcloud CLI
# Follow: https://cloud.google.com/sdk/docs/install

# 2. Initialize and configure
gcloud init
gcloud auth configure-docker

# 3. Build and deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/telegram-spotify-bot
gcloud run deploy telegram-spotify-bot \
  --image gcr.io/YOUR_PROJECT_ID/telegram-spotify-bot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000

# 4. Set environment variables
gcloud run services update telegram-spotify-bot \
  --update-env-vars TELEGRAM_BOT_TOKEN=your_token,SPOTIFY_CLIENT_ID=your_id,...

# 5. Get service URL
gcloud run services describe telegram-spotify-bot --format='value(status.url)'
# Update WEBHOOK_URL with this URL + /webhook
```

## CI/CD with GitHub Actions

The repository includes GitHub Actions workflows:

### 1. CI Workflow (`.github/workflows/ci.yml`)

Runs on every push and PR:
- Code linting with flake8
- Code formatting check with Black
- Type checking with mypy
- Security scanning with Bandit and Safety
- Docker build test

### 2. Docker Publish Workflow (`.github/workflows/docker-publish.yml`)

Runs on:
- Push to main branch
- Version tags (`v*`)
- Releases

Automatically builds and pushes Docker images to GitHub Container Registry.

### Using Published Docker Images

```bash
# Pull the latest image
docker pull ghcr.io/YOUR_USERNAME/telegram-to-spotify-playlist-bot:latest

# Run it
docker run -d \
  --name telegram-spotify-bot \
  --env-file .env \
  -p 8000:8000 \
  ghcr.io/YOUR_USERNAME/telegram-to-spotify-playlist-bot:latest
```

### Setting Up Auto-Deployment

For automatic deployment on push to main:

1. Add deployment secrets to GitHub:
   - `Settings → Secrets and variables → Actions`
   - Add: `HEROKU_API_KEY`, `DIGITALOCEAN_TOKEN`, etc.

2. Create deployment workflow:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Heroku
        env:
          HEROKU_API_KEY: ${{ secrets.HEROKU_API_KEY }}
        run: |
          heroku container:push web -a your-app-name
          heroku container:release web -a your-app-name
```

## Monitoring and Maintenance

### Health Checks

```bash
# Check if bot is running
curl http://localhost:8000/health

# Or with make
make health
```

### Viewing Logs

```bash
# Docker Compose
docker compose logs -f

# Docker
docker logs -f telegram-spotify-bot

# Heroku
heroku logs --tail

# Railway
railway logs
```

### Checking Webhook Status

```bash
# Get webhook info
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo

# Or use the Makefile
make webhook-info
```

### Updating the Bot

```bash
# 1. Pull latest changes
git pull

# 2. Rebuild and restart
make docker-rebuild

# Or for Heroku
git push heroku main
```

### Backup Spotify Authentication

The Spotify authentication token is stored in `.cache-<username>`.

```bash
# Backup
cp .cache-your_username .cache-backup

# Restore
cp .cache-backup .cache-your_username
```

### Common Issues

**Bot not receiving messages:**
1. Check webhook is set correctly:
   ```bash
   curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
   ```
2. Ensure WEBHOOK_URL is HTTPS and publicly accessible
3. Verify chat ID is in ALLOWED_CHAT_IDS

**Spotify authentication failed:**
1. Delete cache file: `rm .cache-*`
2. Re-authenticate: `make auth`
3. Restart bot

**Duplicate tracks:**
1. Bot caches playlist for performance
2. Restart bot to refresh cache

## Security Best Practices

1. **Never commit `.env` file**
   - Use `.env.example` as template
   - Add `.env` to `.gitignore` (already done)

2. **Use secrets management**
   - GitHub Secrets for CI/CD
   - Cloud provider secret managers in production

3. **Restrict chat IDs**
   - Only add trusted group chat IDs to ALLOWED_CHAT_IDS

4. **Use HTTPS**
   - Telegram requires HTTPS for webhooks
   - Use services with built-in SSL (Heroku, Railway, etc.)

5. **Regular updates**
   - Keep dependencies updated
   - Monitor security advisories
   - Use `safety check` regularly

## Performance Optimization

1. **Enable caching**
   - Bot caches playlist contents (already implemented)
   - Cache is invalidated after adding tracks

2. **Batch processing**
   - Bot adds up to 100 tracks per API call (already implemented)

3. **Resource limits**
   - Set appropriate container resource limits in production

4. **Monitoring**
   - Use health check endpoint for uptime monitoring
   - Set up alerts for failures

## Support

For issues:
- Check the [README](README.md)
- Review [GitHub Issues](https://github.com/YOUR_USERNAME/telegram-to-spotify-playlist-bot/issues)
- Create a new issue with logs and configuration (remove sensitive data)
