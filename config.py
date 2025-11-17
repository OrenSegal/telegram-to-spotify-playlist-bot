import os
from typing import List
from pydantic import field_validator, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Configuration settings for the Telegram to Spotify bot."""

    # Telegram settings
    telegram_bot_token: str

    # Spotify settings
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: HttpUrl
    spotify_playlist_id: str
    spotify_username: str

    # Chat control
    allowed_chat_ids: List[int]

    # Bot behavior
    enable_confirmation_messages: bool = False
    enable_error_messages: bool = True

    # Webhook settings
    webhook_url: HttpUrl
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @field_validator("allowed_chat_ids", mode="before")
    @classmethod
    def parse_allowed_chat_ids(cls, v):
        """Parse comma-separated chat IDs from environment variable."""
        if isinstance(v, str):
            return [int(chat_id.strip()) for chat_id in v.split(",") if chat_id.strip()]
        return v
