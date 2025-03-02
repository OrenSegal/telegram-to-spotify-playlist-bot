import os
from typing import List
from pydantic import BaseSettings, validator, HttpUrl

class Config(BaseSettings):
    telegram_bot_token: str
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: HttpUrl
    spotify_playlist_id: str
    allowed_chat_ids: List[int]
    enable_confirmation_messages: bool = False
    enable_error_messages: bool = True
    webhook_url: HttpUrl  # Add webhook URL
    app_host : str = "0.0.0.0"
    app_port : int = 8000
    spotify_username: str # Add spotify username.

    @validator("allowed_chat_ids", pre=True)
    def parse_allowed_chat_ids(cls, v):
        if isinstance(v, str):
            return [int(chat_id.strip()) for chat_id in v.split(",")]
        return v

    class Config:
        env_file = ".env"
