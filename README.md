# tech-8ytees-automation

Fully automated YouTube Shorts & Instagram Reels generation for tech content.

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment variables (see `.env.example`)
3. **YouTube Authentication**: Run `python auth_youtube.py` to generate token.json with proper scopes
4. Run: `python main.py`

## YouTube Setup

To enable YouTube Shorts uploads + pinned comments:

1. **Create OAuth credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Click **Create Credentials** → **OAuth 2.0 Client ID** → **Desktop application**
   - Download and save as `client_secret.json` in the repo root

2. **Generate token.json:**
   ```bash
   python auth_youtube.py
   ```
   This opens your browser to authorize and saves `token.json` with scopes:
   - `youtube` (upload videos + manage comments + pin comments)

3. **GitHub Actions Setup (for automated runs):**
   - Copy entire `token.json` contents
   - Go to GitHub → Settings → **Secrets and variables** → **Actions**
   - Create secret `YOUTUBE_TOKEN_JSON` with the copied contents
   - The workflow automatically writes this to `token.json` before running

## Troubleshooting

### YouTube Daily Upload Limit
New/unverified YouTube channels have a strict daily upload limit. To remove this:
1. Go to [YouTube Studio](https://studio.youtube.com)
2. Click **Settings** → **Channel** → **Feature eligibility**
3. Click **Verify** and complete phone verification
4. Wait 24 hours for the limit to be lifted

### Instagram Upload Issues
See [INSTAGRAM_FIX.md](INSTAGRAM_FIX.md) for detailed setup instructions.

### A/B Testing
See [AB_TESTING.md](AB_TESTING.md) for the A/B testing guide.