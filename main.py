import os
import re
import logging
from typing import Optional, List, Set
from pydantic import ValidationError

import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import spotipy
from spotipy.oauth2 import SpotifyOAuth, CacheFileHandler
from spotipy.exceptions import SpotifyException

from fastapi import FastAPI, Request, HTTPException
import uvicorn

from config import Config

# --- Load Configuration ---
try:
    config = Config()
except ValidationError as e:
    print(f"Configuration error:\n{e}")
    exit(1)

# --- Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Spotify Authentication ---
cache_handler = CacheFileHandler(username=config.spotify_username)
sp_oauth = SpotifyOAuth(
    client_id=config.spotify_client_id,
    client_secret=config.spotify_client_secret,
    redirect_uri=str(config.spotify_redirect_uri),
    scope="playlist-modify-public playlist-modify-private playlist-read-private",
    cache_handler=cache_handler
)
sp = spotipy.Spotify(auth_manager=sp_oauth)

# --- Spotify Link Regex ---
# Matches: track, album, playlist links (both open.spotify.com and spotify.link)
SPOTIFY_LINK_REGEX = re.compile(
    r"https?://(?:open\.spotify\.com|spotify\.link)/(track|album|playlist)/([a-zA-Z0-9]+)(?:\?[^\s]*)?"
)

# --- FastAPI Setup ---
app = FastAPI()

# --- Telegram Bot Application (global) ---
application: Optional[Application] = None


class SpotifyLinkProcessor:
    """Handles processing of different Spotify link types."""

    def __init__(self, spotify_client: spotipy.Spotify, playlist_id: str):
        self.sp = spotify_client
        self.playlist_id = playlist_id
        self._playlist_cache: Optional[Set[str]] = None

    def _get_playlist_tracks(self) -> Set[str]:
        """Get all track URIs currently in the playlist (cached)."""
        if self._playlist_cache is not None:
            return self._playlist_cache

        track_uris = set()
        results = self.sp.playlist_items(self.playlist_id)

        while results:
            for item in results['items']:
                if item['track'] is not None:
                    track_uris.add(item['track']['uri'])

            if results['next']:
                results = self.sp.next(results)
            else:
                break

        self._playlist_cache = track_uris
        return track_uris

    def invalidate_cache(self):
        """Invalidate the playlist cache after adding tracks."""
        self._playlist_cache = None

    def process_track(self, track_id: str) -> tuple[bool, str, Optional[str]]:
        """
        Process a single track link.
        Returns: (success: bool, message: str, track_uri: Optional[str])
        """
        try:
            track = self.sp.track(track_id)
            track_uri = track['uri']
            track_name = track['name']
            artist_name = track['artists'][0]['name']

            playlist_tracks = self._get_playlist_tracks()

            if track_uri in playlist_tracks:
                return False, f"Track '{track_name}' by {artist_name} is already in the playlist", None

            self.sp.playlist_add_items(self.playlist_id, [track_uri])
            self.invalidate_cache()
            logger.info(f"Added track to playlist: {track_uri}")

            return True, f"Added track '{track_name}' by {artist_name}", track_uri

        except SpotifyException as e:
            logger.error(f"Spotify API error for track {track_id}: {e}")
            return False, f"Spotify error: {str(e)}", None
        except Exception as e:
            logger.error(f"Unexpected error processing track {track_id}: {e}")
            return False, f"Error: {str(e)}", None

    def process_album(self, album_id: str) -> tuple[int, int, str]:
        """
        Process an album link by adding all its tracks.
        Returns: (added_count: int, total_count: int, album_name: str)
        """
        try:
            album = self.sp.album(album_id)
            album_name = album['name']
            artist_name = album['artists'][0]['name']

            tracks = album['tracks']['items']
            total_tracks = len(tracks)
            added_count = 0

            playlist_tracks = self._get_playlist_tracks()
            tracks_to_add = []

            for track in tracks:
                track_uri = track['uri']
                if track_uri not in playlist_tracks:
                    tracks_to_add.append(track_uri)

            # Add tracks in batches of 100 (Spotify API limit)
            for i in range(0, len(tracks_to_add), 100):
                batch = tracks_to_add[i:i+100]
                self.sp.playlist_add_items(self.playlist_id, batch)
                added_count += len(batch)

            if added_count > 0:
                self.invalidate_cache()
                logger.info(f"Added {added_count} tracks from album '{album_name}'")

            return added_count, total_tracks, f"{album_name} by {artist_name}"

        except SpotifyException as e:
            logger.error(f"Spotify API error for album {album_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing album {album_id}: {e}")
            raise

    def process_playlist(self, playlist_id: str) -> tuple[int, int, str]:
        """
        Process a playlist link by adding all its tracks.
        Returns: (added_count: int, total_count: int, playlist_name: str)
        """
        try:
            playlist = self.sp.playlist(playlist_id)
            playlist_name = playlist['name']

            target_playlist_tracks = self._get_playlist_tracks()
            tracks_to_add = []

            results = playlist['tracks']
            total_tracks = 0

            while results:
                for item in results['items']:
                    if item['track'] is not None:
                        total_tracks += 1
                        track_uri = item['track']['uri']
                        if track_uri not in target_playlist_tracks:
                            tracks_to_add.append(track_uri)

                if results['next']:
                    results = self.sp.next(results)
                else:
                    break

            # Add tracks in batches of 100
            added_count = 0
            for i in range(0, len(tracks_to_add), 100):
                batch = tracks_to_add[i:i+100]
                self.sp.playlist_add_items(self.playlist_id, batch)
                added_count += len(batch)

            if added_count > 0:
                self.invalidate_cache()
                logger.info(f"Added {added_count} tracks from playlist '{playlist_name}'")

            return added_count, total_tracks, playlist_name

        except SpotifyException as e:
            logger.error(f"Spotify API error for playlist {playlist_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing playlist {playlist_id}: {e}")
            raise


# Initialize processor
processor = SpotifyLinkProcessor(sp, config.spotify_playlist_id)


@app.post("/webhook")
async def webhook(request: Request):
    """Handles incoming webhook requests from Telegram."""
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "ok"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "telegram-spotify-bot"}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    welcome_message = (
        "Hi! I'm your Telegram to Spotify bot.\n\n"
        "I can add Spotify content to your playlist:\n"
        "- Individual tracks\n"
        "- Entire albums\n"
        "- Other playlists\n\n"
        "Just share any Spotify link in the chat, and I'll handle the rest!"
    )
    await update.message.reply_text(welcome_message)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming Telegram messages containing Spotify links."""

    # Check if message exists and is from allowed chat
    if update.message is None or update.message.chat_id not in config.allowed_chat_ids:
        return

    message_text = update.message.text
    if not message_text:
        return

    # Find all Spotify links in the message
    matches = SPOTIFY_LINK_REGEX.findall(message_text)

    if not matches:
        return

    logger.info(f"Found {len(matches)} Spotify link(s) in message from chat {update.message.chat_id}")

    for link_type, item_id in matches:
        try:
            if link_type == "track":
                success, message, _ = processor.process_track(item_id)

                if success and config.enable_confirmation_messages:
                    await update.message.reply_text(f"✅ {message}")
                elif not success and config.enable_error_messages:
                    await update.message.reply_text(f"ℹ️ {message}")

            elif link_type == "album":
                try:
                    added, total, album_name = processor.process_album(item_id)

                    if added > 0:
                        message = f"✅ Added {added}/{total} tracks from album '{album_name}'"
                        if config.enable_confirmation_messages:
                            await update.message.reply_text(message)
                        logger.info(message)
                    else:
                        message = f"ℹ️ All {total} tracks from album '{album_name}' are already in the playlist"
                        if config.enable_confirmation_messages:
                            await update.message.reply_text(message)
                        logger.info(message)

                except Exception as e:
                    error_msg = f"Error processing album: {str(e)}"
                    logger.error(error_msg)
                    if config.enable_error_messages:
                        await update.message.reply_text(f"❌ {error_msg}")

            elif link_type == "playlist":
                try:
                    added, total, playlist_name = processor.process_playlist(item_id)

                    if added > 0:
                        message = f"✅ Added {added}/{total} tracks from playlist '{playlist_name}'"
                        if config.enable_confirmation_messages:
                            await update.message.reply_text(message)
                        logger.info(message)
                    else:
                        message = f"ℹ️ All {total} tracks from playlist '{playlist_name}' are already in the playlist"
                        if config.enable_confirmation_messages:
                            await update.message.reply_text(message)
                        logger.info(message)

                except Exception as e:
                    error_msg = f"Error processing playlist: {str(e)}"
                    logger.error(error_msg)
                    if config.enable_error_messages:
                        await update.message.reply_text(f"❌ {error_msg}")

        except Exception as e:
            logger.error(f"Unexpected error handling {link_type} link: {e}")
            if config.enable_error_messages:
                await update.message.reply_text(f"❌ An unexpected error occurred: {str(e)}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")


async def setup_bot():
    """Initialize the bot application."""
    global application

    application = Application.builder().token(config.telegram_bot_token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    # Initialize the application
    await application.initialize()
    await application.start()

    # Set webhook
    webhook_url = str(config.webhook_url)
    await application.bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")


async def shutdown_bot():
    """Cleanup bot resources."""
    if application:
        await application.stop()
        await application.shutdown()


@app.on_event("startup")
async def startup_event():
    """FastAPI startup event."""
    await setup_bot()
    logger.info("Bot started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """FastAPI shutdown event."""
    await shutdown_bot()
    logger.info("Bot shutdown complete")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.app_host,
        port=config.app_port,
        log_level="info"
    )
