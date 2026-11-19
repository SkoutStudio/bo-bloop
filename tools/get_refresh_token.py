#!/usr/bin/env python3
"""Create the YouTube refresh token for the Bo & Bloop channel (run on YOUR computer, not in the cloud).

  pip install google-auth-oauthlib
  python get_refresh_token.py

It asks for the OAuth Client ID and Client secret (same ones as Curious Engine), opens the browser,
you log in and pick the **Bo & Bloop** channel, and it prints the refresh token to paste into the
GitHub secret YT_REFRESH_TOKEN_BO_BLOOP. Nothing is saved or sent anywhere else.
"""
import getpass

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

cid = input("YT_CLIENT_ID: ").strip()
secret = getpass.getpass("YT_CLIENT_SECRET (δεν φαίνεται όταν γράφεις): ").strip()
flow = InstalledAppFlow.from_client_config(
    {"installed": {"client_id": cid, "client_secret": secret,
                   "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                   "token_uri": "https://oauth2.googleapis.com/token",
                   "redirect_uris": ["http://localhost"]}},
    SCOPES)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent",
                              authorization_prompt_message="Ανοίγει ο browser: διάλεξε το κανάλι Bo & Bloop.")
print("\nYT_REFRESH_TOKEN_BO_BLOOP =\n" + creds.refresh_token)
