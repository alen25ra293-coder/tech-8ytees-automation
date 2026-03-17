"""
VPN/Proxy setup for Instagram uploads.
Changes the IP address to avoid blacklisting.

Options:
1. Bright Data (formerly Luminati) - Residential proxies
2. Oxylabs - High-quality rotating proxies
3. WireGuard VPN - Self-hosted or commercial
"""

import os
import requests
from datetime import datetime

def get_rotating_proxy():
    """
    Get rotating proxy credentials from environment.
    
    Environment Variables Needed:
    - PROXY_TYPE: "bright_data", "oxylabs", "residential", or "vpn"
    - PROXY_HOST: proxy server hostname
    - PROXY_PORT: proxy port
    - PROXY_USER: proxy username
    - PROXY_PASS: proxy password
    """
    proxy_type = os.environ.get("PROXY_TYPE", "").lower()
    
    if proxy_type == "bright_data":
        # Bright Data format
        username = os.environ.get("BRIGHT_DATA_USER")
        password = os.environ.get("BRIGHT_DATA_PASS")
        host = os.environ.get("BRIGHT_DATA_HOST", "zproxy.lum-superproxy.io")
        port = os.environ.get("BRIGHT_DATA_PORT", "22225")
        
        proxy_url = f"http://{username}:{password}@{host}:{port}"
        return {"http": proxy_url, "https": proxy_url}
    
    elif proxy_type == "oxylabs":
        # Oxylabs format
        username = os.environ.get("OXYLABS_USER")
        password = os.environ.get("OXYLABS_PASS")
        host = os.environ.get("OXYLABS_HOST", "pr.oxylabs.io")
        port = os.environ.get("OXYLABS_PORT", "7777")
        
        proxy_url = f"http://{username}:{password}@{host}:{port}"
        return {"http": proxy_url, "https": proxy_url}
    
    else:
        # Generic proxy format
        host = os.environ.get("PROXY_HOST")
        port = os.environ.get("PROXY_PORT")
        user = os.environ.get("PROXY_USER")
        password = os.environ.get("PROXY_PASS")
        
        if host and port:
            if user and password:
                proxy_url = f"http://{user}:{password}@{host}:{port}"
            else:
                proxy_url = f"http://{host}:{port}"
            return {"http": proxy_url, "https": proxy_url}
    
    return None


def upload_via_proxy(video_path, caption, upload_function):
    """
    Wrapper to execute upload through a rotating proxy.
    Avoids IP blacklisting by changing IP for each request.
    
    Args:
        video_path: Path to video file
        caption: Video caption
        upload_function: The upload function to call with proxy
    
    Returns:
        True if successful, False otherwise
    """
    proxies = get_rotating_proxy()
    
    if not proxies:
        print("⚠️ No proxy configured. Skipping proxy-based upload.")
        return False
    
    print("🔄 Using rotating proxy to change IP address...")
    print(f"   Proxy: {proxies.get('http', 'unknown')[:50]}...")
    
    try:
        # Call the upload function with proxy
        result = upload_function(video_path, caption, proxies=proxies)
        return result
    except Exception as e:
        print(f"❌ Proxy upload failed: {e}")
        return False


def setup_wireguard_vpn():
    """
    Setup instructions for WireGuard VPN in GitHub Actions.
    This automatically rotates the IP for uploads.
    """
    return """
🔐 WireGuard VPN Setup for GitHub Actions
──────────────────────────────────────────

Option A: Use a VPN Service (Easier)
────────────────────────────────────
Services with API support:
- Mullvad VPN (free, no account needed)
- ProtonVPN (paid, API available)
- NordVPN (paid with NordLynx)

Example: Mullvad VPN in GitHub Actions

.github/workflows/daily_upload.yml:
```yaml
- name: Setup Mullvad VPN
  uses: mullvad/github-actions@v1.1.0
  with:
    dns-enabled: true
    region: us  # Change region for different IP

- name: Verify IP changed
  run: curl https://api.mullvad.net/ip

- name: 🚀 Run automation (through VPN)
  run: python main.py
```

Option B: Self-Hosted WireGuard
───────────────────────────────
1. Create a WireGuard server (cheap VPS: $3-5/month)
2. Store VPN config in GitHub Secrets
3. Connect to VPN before running script

Cost: $3-5/month for VPS


Option C: Bright Data Rotating Proxy
────────────────────────────────────
1. Sign up: https://brightdata.com
2. Get residential proxy credentials
3. Set GitHub Secrets:
   - BRIGHT_DATA_USER=your_user
   - BRIGHT_DATA_PASS=your_pass
   - PROXY_TYPE=bright_data

Cost: $3.60-7/GB (cheap for occasional use)


RECOMMENDED FOR YOUR USE CASE:
Use Mullvad (free) + GitHub Actions
- Free
- Works great
- No credentials needed
- Automatic IP rotation per workflow run
"""


def get_proxy_github_actions_workflow():
    """Return example GitHub Actions workflow with proxy setup"""
    return """
name: Tech 8ytees Daily Upload (with Proxy)

on:
  schedule:
    - cron: '0 0 * * *'
  workflow_dispatch:

jobs:
  upload:
    runs-on: ubuntu-latest
    timeout-minutes: 45

    steps:
      - uses: actions/checkout@v4
      
      - name: 🌐 Setup Mullvad VPN (Free IP Rotation)
        uses: mullvad/github-actions@v1.1.0
        with:
          dns-enabled: true
          region: us  # Changes IP for each run
      
      - name: 🔍 Verify IP changed
        run: curl -s https://api.mullvad.net/ip | jq '.ip'
      
      - name: 🐍 Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: 📦 Install dependencies
        run: |
          sudo apt-get update -qq
          sudo apt-get install -y ffmpeg fonts-liberation imagemagick
          pip install -r requirements.txt
      
      - name: 🚀 Run automation (through VPN)
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEYS }}
          IG_BUSINESS_ACCOUNT_ID: ${{ secrets.IG_BUSINESS_ACCOUNT_ID }}
          IG_GRAPH_ACCESS_TOKEN: ${{ secrets.IG_GRAPH_ACCESS_TOKEN }}
          YOUTUBE_TOKEN_JSON: ${{ secrets.YOUTUBE_TOKEN_JSON }}
          PEXELS_API_KEY: ${{ secrets.PEXELS_API_KEY }}
        run: python main.py
      
      - name: 🧹 Cleanup
        if: always()
        run: rm -f output.mp4 voiceover.mp3 subtitles.vtt token.json
"""
