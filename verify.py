#!/usr/bin/env python3
"""
Verification script to check if the bot is properly configured and ready to deploy.
"""

import os
import sys
import re
from pathlib import Path


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_header(text):
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_success(text):
    print(f"{Colors.GREEN}✓{Colors.END} {text}")


def print_error(text):
    print(f"{Colors.RED}✗{Colors.END} {text}")


def print_warning(text):
    print(f"{Colors.YELLOW}!{Colors.END} {text}")


def check_file_exists(filepath, required=True):
    """Check if a file exists."""
    if Path(filepath).exists():
        print_success(f"{filepath} exists")
        return True
    else:
        if required:
            print_error(f"{filepath} not found (required)")
        else:
            print_warning(f"{filepath} not found (optional)")
        return False


def check_env_file():
    """Check if .env file is properly configured."""
    print_header("Environment Configuration")

    if not check_file_exists(".env"):
        print_error("Create .env file using .env.example as template")
        return False

    # Read .env file
    with open(".env", "r") as f:
        env_content = f.read()

    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "SPOTIFY_CLIENT_ID",
        "SPOTIFY_CLIENT_SECRET",
        "SPOTIFY_REDIRECT_URI",
        "SPOTIFY_PLAYLIST_ID",
        "SPOTIFY_USERNAME",
        "ALLOWED_CHAT_IDS",
        "WEBHOOK_URL",
    ]

    placeholder_patterns = [
        "YOUR_TELEGRAM_BOT_TOKEN",
        "your_spotify_client_id",
        "your_spotify_client_secret",
        "your_playlist_id",
        "your_spotify_username",
        "your-domain.com",
    ]

    all_good = True
    for var in required_vars:
        if var in env_content:
            # Check if it's still a placeholder
            value = re.search(f"{var}=(.+)", env_content)
            if value:
                val = value.group(1).strip()
                if any(placeholder in val for placeholder in placeholder_patterns):
                    print_error(f"{var} has placeholder value: {val}")
                    all_good = False
                else:
                    print_success(f"{var} is configured")
            else:
                print_error(f"{var} is empty")
                all_good = False
        else:
            print_error(f"{var} not found in .env")
            all_good = False

    return all_good


def check_dependencies():
    """Check if required dependencies can be imported."""
    print_header("Python Dependencies")

    dependencies = [
        ("telegram", "python-telegram-bot"),
        ("spotipy", "spotipy"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("pydantic", "pydantic"),
        ("pydantic_settings", "pydantic-settings"),
    ]

    all_good = True
    for module, package in dependencies:
        try:
            __import__(module)
            print_success(f"{package} installed")
        except ImportError:
            print_error(f"{package} not installed")
            all_good = False

    if not all_good:
        print(f"\n{Colors.YELLOW}Run: pip install -r requirements.txt{Colors.END}")

    return all_good


def check_code_syntax():
    """Check if main modules can be imported."""
    print_header("Code Validation")

    # Set dummy environment variables for import test
    os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token")
    os.environ.setdefault("SPOTIFY_CLIENT_ID", "test_id")
    os.environ.setdefault("SPOTIFY_CLIENT_SECRET", "test_secret")
    os.environ.setdefault("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
    os.environ.setdefault("SPOTIFY_PLAYLIST_ID", "test_playlist")
    os.environ.setdefault("SPOTIFY_USERNAME", "test_user")
    os.environ.setdefault("ALLOWED_CHAT_IDS", "-1001234567890")
    os.environ.setdefault("WEBHOOK_URL", "https://example.com/webhook")

    try:
        import config
        print_success("config.py imports successfully")
    except Exception as e:
        print_error(f"config.py import failed: {e}")
        return False

    try:
        # Don't actually import main as it tries to connect to Spotify
        with open("main.py", "r") as f:
            compile(f.read(), "main.py", "exec")
        print_success("main.py syntax is valid")
    except Exception as e:
        print_error(f"main.py syntax error: {e}")
        return False

    return True


def check_required_files():
    """Check if all required files exist."""
    print_header("Required Files")

    files = {
        "main.py": True,
        "config.py": True,
        "requirements.txt": True,
        "Dockerfile": True,
        "docker-compose.yml": True,
        ".gitignore": True,
        "README.md": True,
        ".env": True,
        ".env.example": False,
        "setup.sh": False,
        "Makefile": False,
    }

    all_required = True
    for filepath, required in files.items():
        exists = check_file_exists(filepath, required)
        if required and not exists:
            all_required = False

    return all_required


def check_docker():
    """Check if Docker is available."""
    print_header("Docker Setup")

    import subprocess

    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print_success(f"Docker installed: {result.stdout.strip()}")
            docker_available = True
        else:
            print_error("Docker is installed but not working properly")
            docker_available = False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print_warning("Docker not found (optional for deployment)")
        docker_available = False

    # Check docker-compose
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print_success(f"Docker Compose installed: {result.stdout.strip()}")
        else:
            # Try old docker-compose
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print_success(f"Docker Compose installed: {result.stdout.strip()}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        if docker_available:
            print_warning("Docker Compose not found (optional)")

    return True  # Not critical


def check_spotify_auth():
    """Check if Spotify authentication cache exists."""
    print_header("Spotify Authentication")

    # Look for cache files
    cache_files = list(Path(".").glob(".cache-*"))

    if cache_files:
        print_success(f"Spotify auth cache found: {cache_files[0].name}")
        print_warning("Copy this file to production or re-authenticate there")
        return True
    else:
        print_warning("No Spotify auth cache found")
        print(f"{Colors.YELLOW}Run: python -c 'from main import sp; print(sp.current_user())'{Colors.END}")
        return False


def main():
    """Run all verification checks."""
    print_header("Telegram to Spotify Bot - Verification")

    checks = [
        ("Required Files", check_required_files),
        ("Environment Configuration", check_env_file),
        ("Python Dependencies", check_dependencies),
        ("Code Validation", check_code_syntax),
        ("Docker Setup", check_docker),
        ("Spotify Authentication", check_spotify_auth),
    ]

    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print_error(f"Check failed with error: {e}")
            results[name] = False

    # Print summary
    print_header("Verification Summary")

    passed = sum(results.values())
    total = len(results)

    for name, result in results.items():
        if result:
            print_success(name)
        else:
            print_error(name)

    print(f"\n{Colors.BLUE}{'─' * 60}{Colors.END}")
    if passed == total:
        print(f"{Colors.GREEN}All checks passed! ({passed}/{total}){Colors.END}")
        print(f"{Colors.GREEN}Your bot is ready to deploy! 🚀{Colors.END}")
        sys.exit(0)
    else:
        print(f"{Colors.YELLOW}Some checks failed ({passed}/{total}){Colors.END}")
        print(f"{Colors.YELLOW}Please fix the issues above before deploying.{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()
