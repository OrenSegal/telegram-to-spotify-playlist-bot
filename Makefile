.PHONY: help install auth build up down logs restart clean test lint format

help:
	@echo "Telegram to Spotify Bot - Make Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    - Install Python dependencies"
	@echo "  make auth       - Authenticate with Spotify"
	@echo "  make build      - Build Docker image"
	@echo "  make up         - Start the bot with Docker Compose"
	@echo "  make down       - Stop the bot"
	@echo "  make logs       - View bot logs"
	@echo "  make restart    - Restart the bot"
	@echo "  make clean      - Clean up containers and cache"
	@echo "  make test       - Run tests and checks"
	@echo "  make lint       - Run linters"
	@echo "  make format     - Format code with Black"
	@echo "  make run        - Run bot locally (no Docker)"

install:
	pip install -r requirements.txt

auth:
	@echo "Setting up Spotify authentication..."
	python -c "from main import sp; print('User:', sp.current_user()['display_name'])"

build:
	docker compose build

up:
	@mkdir -p cache
	docker compose up -d
	@echo "Bot started! View logs with: make logs"

down:
	docker compose down

logs:
	docker compose logs -f

restart:
	docker compose restart

clean:
	docker compose down -v
	rm -rf cache __pycache__ .pytest_cache
	find . -type f -name "*.pyc" -delete

test:
	@echo "Running basic checks..."
	python -c "from config import Config; print('✓ Config validation passed')"
	@echo "✓ All checks passed!"

lint:
	@echo "Running linters..."
	-flake8 main.py config.py --max-line-length=127
	-mypy main.py config.py --ignore-missing-imports

format:
	black main.py config.py

run:
	python main.py

# Docker-specific commands
docker-shell:
	docker compose exec telegram-bot /bin/bash

docker-rebuild:
	docker compose build --no-cache
	docker compose up -d

# Deployment helpers
deploy-heroku:
	@echo "Deploying to Heroku..."
	heroku container:push web
	heroku container:release web

webhook-info:
	@echo "Checking Telegram webhook status..."
	@python -c "import os; token = os.getenv('TELEGRAM_BOT_TOKEN', 'TOKEN'); print(f'curl https://api.telegram.org/bot{token}/getWebhookInfo')"

health:
	@curl -s http://localhost:8000/health | python -m json.tool || echo "Bot is not running"
