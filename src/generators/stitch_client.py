import os
import requests
import time
import json

def generate_ui_image(prompt: str, output_path: str = "output_ui.jpg") -> str | None:
    """
    Calls the Google Stitch API via MCP to generate a UI / screenshot.
    Returns the path to the saved image, or None if it fails.
    """
    api_key = os.environ.get("STITCH_API_KEY", "").strip()
    if not api_key:
        print("⚠️  STITCH_API_KEY not found in environment. Skipping Stitch generation.")
        return None

    print(f"🪄  Prompting Stitch API: '{prompt[:60]}...'")

    endpoint = "https://stitch.withgoogle.com/api/mcp"
    project_id = "tech-8ytees-shorts"
    
    # 1. Instruct the Stitch MCP server to create a screen from text
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "create_screen_from_text",
            "arguments": {
                "projectId": project_id,
                "text": prompt,
                "deviceType": "mobile",
                "modelId": "nemo-latest"
            }
        }
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                print(f"❌ Stitch API returned JSON-RPC error: {data['error']}")
                return None
                
            # Usually returns a list of content blocks in result.content
            # The tool should give us the screenId
            print("Response from create_screen_from_text:", json.dumps(data, indent=2))
            
            # TODO: We need to parse screenId and poll `get_screen_image`.
            # For now, just save if there's raw image data directly or implement polling logic later once we verify the response.
            print("⚠️ Need the user's STITCH_API_KEY to test the actual API response and finalize the parsing logic.")
            return None
            
        else:
            print(f"⚠️ Stitch API returned status {response.status_code}: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Stitch API network error: {e}")
        return None
