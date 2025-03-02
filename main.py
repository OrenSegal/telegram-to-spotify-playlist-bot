import os
import re
import logging
from typing import Optional
from pydantic import ValidationError

import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import spotipy
from spotipy.oauth2 import SpotifyOAuth, CacheFileHandler

from fastapi import FastAPI, Request
import uvicorn

from config import Config  # Import the Config class

# --- Load Configuration (using Pydantic) ---
try:
    config = Config()
except ValidationError as e:
    print(f"Configuration error:\n{e}")
    exit(1)

# --- Logging ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Spotify Authentication ---
cache_handler = CacheFileHandler(username=config.spotify_username)
sp_oauth = SpotifyOAuth(client_id=config.spotify_client_id,
                        client_secret=config.spotify_client_secret,
                        redirect_uri=str(config.spotify_redirect_uri),  # Convert HttpUrl to str
                        scope="playlist-modify-public playlist-read-private",
                        cache_handler=cache_handler)
sp = spotipy.Spotify(auth_manager=sp_oauth)

# --- Spotify Link Regex ---
SPOTIFY_TRACK_REGEX = re.compile(r"(https?://(?:open\.spotify\.com|spotify\.link)/(?:track|playlist)/([a-zA-Z0-9]+)(?:\?[^\s]*)?)")

# --- FastAPI Setup ---
app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    """Handles incoming webhook requests from Telegram."""
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)  # Use application.bot
        await application.process_update(update) # Process the update.
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}")
    return {"status": "ok"}

# --- Telegram Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    await update.message.reply_text(
        "Hi! I'm a bot that adds Spotify music tracks to a playlist. I work silently in the background. "
        "Just send Spotify track links in this chat, and I'll add them.  "
        "Confirmation/error messages are enabled based on the bot's configuration."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming Telegram messages (same logic as before, but async)."""
    if update.message is None or update.message.chat_id not in config.allowed_chat_ids:
        return

    message_text = update.message.text
    if not message_text:
        return

    matches = SPOTIFY_TRACK_REGEX.findall(message_text)

    for full_url, track_id in matches:
        try:
            track = sp.track(track_id)
            if track['type'] != 'track':
                logger.info(f"Ignoring non-track link: {full_url}")
                continue

            track_uri = track['uri']
            playlist_tracks = sp.playlist_items(config.spotify_playlist_id)
            track_uris_in_playlist = [item['track']['uri'] for item in playlist_tracks['items'] if item['track'] is not None]

            if track_uri in track_uris_in_playlist:
                logger.info(f"Track already in playlist: {track_uri}")
                if config.enable_confirmation_messages:
                    await update.message.reply_text(f"Track {track['name']} by {track['artists'][0]['name']} already in the playlist!")
                continue

            sp.playlist_add_items(config.spotify_playlist_id, [track_uri])
            logger.info(f"Added track to playlist: {track_uri}")
            if config.enable_confirmation_messages:
                await update.message.reply_text(f"Added track {track['name']} by {track['artists'][0]['name']} to the playlist!")

        except spotipy.SpotifyException as e:
            logger.error(f"Spotify API error: {e}")
            if config.enable_error_messages:
                await update.message.reply_text(f"Error adding track: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            if config.enable_error_messages:
                await update.message.reply_text(f"An unexpected error occurred: {e}")



# --- Main Application Setup ---
application = Application.builder().token(config.telegram_bot_token).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


async def run_webhook():

    # Set the webhook
    await application.bot.set_webhook(url=str(config.webhook_url)) # Convert to str
    # Run FastAPI server using uvicorn.
    config_fastapi = uvicorn.Config(
        "main:app", host=config.app_host, port=config.app_port, log_level="info", reload=False
        )
    server = uvicorn.Server(config_fastapi)
    await server.serve()


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_webhook())
