"""
One-Time YouTube OAuth 2.0 Token Generation Utility.
Run this script locally ONCE on a computer with a web browser to authorize
your YouTube channel and obtain your permanent YOUTUBE_REFRESH_TOKEN.
"""

import os
import sys
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    print("=" * 70)
    print(" YOUTUBE OAUTH 2.0 REFRESH TOKEN GENERATOR")
    print("=" * 70)

    # Search for client_secret.json
    base_dir = Path(__file__).resolve().parent.parent
    possible_paths = [
        Path("client_secret.json"),
        base_dir / "client_secret.json",
        Path("client_secrets.json"),
        base_dir / "client_secrets.json",
    ]

    secret_file = None
    for p in possible_paths:
        if p.exists() and p.is_file():
            secret_file = p
            break

    if not secret_file:
        print("\n[!] 'client_secret.json' not found in current directory or project root.")
        user_input = input("Enter path to your downloaded client secret JSON file: ").strip()
        secret_file = Path(user_input.strip('"').strip("'"))
        if not secret_file.exists():
            print(f"[X] File not found at: {secret_file}")
            print("Please download it from Google Cloud Console -> APIs & Services -> Credentials.")
            sys.exit(1)

    print(f"\n[+] Using credentials file: {secret_file}")
    with open(secret_file, "r", encoding="utf-8") as f:
        client_data = json.load(f)

    print("[+] Launching local authentication server on port 8080...")
    print("    A browser window will open. Sign in with the Google Account that owns your YouTube channel.")
    print("    If a warning 'Google hasn't verified this app' appears, click 'Advanced' -> 'Go to app (unsafe)' to proceed.")

    flow = InstalledAppFlow.from_client_secrets_file(str(secret_file), SCOPES)
    credentials = flow.run_local_server(
        port=8080,
        prompt="consent",
        access_type="offline"
    )

    if not credentials.refresh_token:
        print("\n[!] WARNING: No refresh token returned. Did you click 'Allow' and ensure prompt='consent'?")
        print("    If you already authorized previously, revoke access at:")
        print("    https://myaccount.google.com/permissions and run this script again.")
        sys.exit(1)

    # Minify client secret json for environment variable
    minified_json = json.dumps(client_data, separators=(',', ':'))

    print("\n" + "=" * 70)
    print(" SUCCESS! COPY THE VALUES BELOW INTO YOUR .env OR GITHUB SECRETS")
    print("=" * 70)
    print("\n1. YOUTUBE_REFRESH_TOKEN:")
    print(credentials.refresh_token)
    print("\n2. YOUTUBE_CLIENT_SECRET_JSON (Full minified JSON string):")
    print(minified_json)
    print("\n" + "=" * 70)

    # Optional automatic .env updater
    env_file = base_dir / ".env"
    if env_file.exists():
        update = input("\nWould you like to automatically write these to your local .env file? [y/N]: ").strip().lower()
        if update == "y":
            with open(env_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            new_lines = []
            has_token = False
            has_secret = False
            for line in lines:
                if line.startswith("YOUTUBE_REFRESH_TOKEN="):
                    new_lines.append(f"YOUTUBE_REFRESH_TOKEN={credentials.refresh_token}\n")
                    has_token = True
                elif line.startswith("YOUTUBE_CLIENT_SECRET_JSON="):
                    new_lines.append(f"YOUTUBE_CLIENT_SECRET_JSON='{minified_json}'\n")
                    has_secret = True
                else:
                    new_lines.append(line)
            
            if not has_token:
                new_lines.append(f"\nYOUTUBE_REFRESH_TOKEN={credentials.refresh_token}\n")
            if not has_secret:
                new_lines.append(f"YOUTUBE_CLIENT_SECRET_JSON='{minified_json}'\n")
                
            with open(env_file, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            print("[+] Updated local .env successfully!")


if __name__ == "__main__":
    main()
