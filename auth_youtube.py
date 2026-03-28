"""
YouTube OAuth Authentication — Tech 8ytees
Generates token.json with required scopes for upload + commenting.
Run this once to generate the token, then paste it into GitHub Actions secrets.
"""
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# Required scopes: upload videos + manage comments
SCOPES = [
    "https://www.googleapis.com/auth/youtube",  # Full YouTube access (includes upload + comment)
]

def authenticate():
    """Generate token.json with proper scopes."""
    if not os.path.exists("client_secret.json"):
        print("❌ client_secret.json not found!")
        print("   Get it from: https://console.cloud.google.com/apis/credentials")
        print("   Download OAuth 2.0 Client IDs (Desktop app)")
        return None

    # Create the OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json",
        scopes=SCOPES,
        redirect_uri="http://localhost:8080/"
    )

    # Get credentials (opens browser for login)
    creds = flow.run_local_server(port=8080)

    # Save to token.json
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
        "universe_domain": creds.universe_domain,
    }

    with open("token.json", "w") as f:
        json.dump(token_data, f, indent=2)

    print("✅ token.json created successfully!")
    print("📋 Scopes granted:")
    for scope in creds.scopes:
        print(f"   • {scope}")
    print("\n💾 Save token.json contents to GitHub Actions secret 'YOUTUBE_TOKEN_JSON'")
    print("   GitHub → Settings → Secrets and variables → Actions → New repository secret")

if __name__ == "__main__":
    authenticate()
