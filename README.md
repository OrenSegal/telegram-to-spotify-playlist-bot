# telegram-to-spotify-playlist-bot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Heroku](https://img.shields.io/badge/heroku-%23430098.svg?style=flat&logo=heroku&logoColor=white)](https://www.heroku.com/)


This Telegram bot automatically adds Spotify music track links shared in a Telegram group to a designated Spotify playlist.  It's designed to be unobtrusive, running silently in the background. It leverages the Telegram Bot API and the Spotify API (via Spotipy) for seamless integration.

## Features

*   **Automatic Spotify Track Detection:** Monitors specified Telegram groups for Spotify track links (both full `open.spotify.com` and shortened `spotify.link` URLs).
*   **Playlist Management:** Adds detected tracks to a pre-defined Spotify playlist.
*   **Duplicate Prevention:**  Checks for and avoids adding duplicate tracks to the playlist.
*   **Error Handling:** Gracefully handles various error conditions (invalid links, API errors, network issues) with logging.
*   **Configuration:**  Easy configuration via environment variables (using a `.env` file).
*   **Deployment Ready:** Includes a `Dockerfile` for easy containerization and deployment (e.g., to Heroku, AWS, Google Cloud).
*   **OAuth 2.0 Authentication:** Securely authenticates with the Spotify API using OAuth 2.0.
*   **Token Persistence:** Stores Spotify API tokens, so re-authorization isn't needed every time.
*   **Multi-Group Support:**  Can be configured to monitor multiple Telegram groups.
*   **Optional Messaging:** Can be configured to send confirmation or error messages to the Telegram group (disabled by default).

## Prerequisites

*   **Python 3.7+:** The bot is written in Python.
*   **Telegram Bot Token:** You'll need to create a Telegram bot and obtain its API token. Follow the instructions on the [Telegram Bot API documentation](https://core.telegram.org/bots#6-botfather).
*   **Spotify Developer Account:** Create a Spotify developer account and register a new application at [developer.spotify.com](https://developer.spotify.com/dashboard/applications).  You'll need the Client ID and Client Secret.
*   **Spotify Playlist ID:**  Create a Spotify playlist (or use an existing one) and note its ID.  The playlist ID can be found in the playlist's URL (e.g., `https://open.spotify.com/playlist/YOUR_PLAYLIST_ID`).
*   **Docker (Optional, but Recommended):** For containerized deployment.
*   **Heroku Account (Optional):** For deployment to Heroku.  You can also deploy to other cloud platforms or a VPS.

## Setup and Configuration

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/YOUR_USERNAME/telegram-spotify-playlist-bot.git
    cd telegram-spotify-playlist-bot
    ```

2.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Create a `.env` File:** Create a `.env` file in the project root directory and add the following environment variables:

    ```
    TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
    SPOTIFY_CLIENT_ID=YOUR_SPOTIFY_CLIENT_ID
    SPOTIFY_CLIENT_SECRET=YOUR_SPOTIFY_CLIENT_SECRET
    SPOTIFY_REDIRECT_URI=http://localhost:8888/callback  # Or your deployed URL
    SPOTIFY_PLAYLIST_ID=YOUR_SPOTIFY_PLAYLIST_ID
    ALLOWED_CHAT_IDS=-1001234567890,-1009876543210  # Comma-separated list of chat IDs
    ENABLE_CONFIRMATION_MESSAGES=False  # Set to True to send confirmation messages
    ENABLE_ERROR_MESSAGES=True # Set to True to send error messages
    ```
    *   **`TELEGRAM_BOT_TOKEN`:**  Your Telegram bot token.
    *   **`SPOTIFY_CLIENT_ID`:** Your Spotify application's Client ID.
    *   **`SPOTIFY_CLIENT_SECRET`:**  Your Spotify application's Client Secret.
    *   **`SPOTIFY_REDIRECT_URI`:**  The redirect URI you specified when creating your Spotify application. For local testing, `http://localhost:8888/callback` is often used.  For deployment, this should be the URL of your deployed application (e.g., your Heroku app's URL).
    *   **`SPOTIFY_PLAYLIST_ID`:** The ID of the Spotify playlist you want to add tracks to.
    *   **`ALLOWED_CHAT_IDS`:** A comma-separated list of Telegram chat IDs (numeric) where the bot should listen for Spotify links.  Get the chat ID by adding a bot like `@myidbot` to your group.
    *  **`ENABLE_CONFIRMATION_MESSAGES`:** Whether the bot posts to the group when a track is added.
    *   **`ENABLE_ERROR_MESSAGES`:** Whether the bot should send error messages to the Telegram group.
    *  **Important Security Note: Do NOT commit your `.env` file to version control (it's included in `.gitignore`).**

4. **Replace `your_spotify_username`**: Replace `your_spotify_username` in `main.py` with your Spotify username.

## Running the Bot Locally

1.  **Run `main.py`:**

    ```bash
    python main.py
    ```

2.  **First Run (Spotify Authentication):** The first time you run the bot, it will open a web browser window to prompt you to authorize the application with your Spotify account.  This is part of the OAuth 2.0 flow.  Once authorized, a token will be stored locally (using Spotipy's `CacheFileHandler`) to avoid needing to re-authorize every time.

## Deployment (Docker & Heroku Example)

These instructions provide a basic example of deploying to Heroku using Docker.  You can adapt these steps for other deployment platforms.

1.  **Install Docker:**  Make sure you have Docker installed and running on your system.
2.  **Install Heroku CLI:** Install the Heroku Command Line Interface.
3.  **Create a Heroku App:**  Create a new app on your Heroku dashboard.
4.  **Build the Docker Image:**

    ```bash
    docker build -t telegram-spotify-bot .
    ```

5.  **Login to Heroku and Container Registry:**

    ```bash
    heroku login
    heroku container:login
    ```

6.  **Push the Docker Image to Heroku:**

    ```bash
    heroku container:push web -a your-heroku-app-name
    ```
     (Replace `your-heroku-app-name` with the name of your Heroku app).

7.  **Release the Image:**

    ```bash
    heroku container:release web -a your-heroku-app-name
    ```

8.  **Set Environment Variables:**
    *   Go to your Heroku app's settings page in the Heroku dashboard.
    *   Click "Reveal Config Vars."
    *   Add all the environment variables from your `.env` file (TELEGRAM_BOT_TOKEN, SPOTIFY_CLIENT_ID, etc.) as key-value pairs.

9. **Start the Bot:**
    ```bash
    heroku ps:scale web=1 -a your-heroku-app-name
    ```

## Webhooks (Recommended for Production)

The provided code uses long polling for simplicity.  For production deployments, **webhooks are strongly recommended** for improved performance and scalability.  To use webhooks, you'll need to:

1.  **Set up a Web Server:** Modify the code to use a web framework like Flask or FastAPI to create a web server that can receive POST requests from Telegram.
2.  **Expose the Server:** Make your web server accessible from the internet.  For development, you can use a tool like ngrok.  For production, you'll need a publicly accessible URL (e.g., by deploying your server to a cloud platform).
3.  **Configure Telegram:**  Use the `setWebhook` method of the Telegram Bot API to tell Telegram to send updates to your webhook URL.  See the `python-telegram-bot` documentation for details on using webhooks.  You'll need to adapt `main.py` to use `Application` instead of `Updater`.
4. Replace `updater.start_polling()` by `application.run_webhook()` with all the required parameters.

## Contributing

Contributions are welcome!  Please feel free to submit pull requests or open issues for bug reports or feature requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
Use code with caution.
Markdown
Key improvements and explanations in this README:

Clear and Concise Introduction: Explains the bot's purpose and key features upfront.

Prerequisites: Lists all necessary software and accounts.

Detailed Setup Instructions: Provides step-by-step instructions for setting up the bot, including creating the .env file and explaining each environment variable.

Local Running Instructions: Explains how to run the bot locally for testing and development.

Deployment Instructions (Docker & Heroku): Provides a clear example of deploying the bot using Docker and Heroku. This is the recommended deployment method.

Webhooks Explanation: Clearly explains the importance of webhooks for production and provides a high-level overview of how to implement them. This is crucial for scalability.

Security Note: Emphasizes the importance of not committing the .env file to version control.

Contributing Section: Encourages contributions and provides guidance.

License: Specifies the project's license (MIT in this case).

Badges: Includes badges for license, Python version, Docker, and Heroku, making the project look more professional.

Spotify Username: Instructions to add user's Spotify Username.

Clear separation of Local Running and Heroku Deployment.
