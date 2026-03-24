import os
import requests
import time
import json
import base64

def generate_ui_image(prompt: str, output_path: str = "output_ui.jpg") -> str | None:
    """
    Calls the Google Stitch API via MCP to generate a UI / screenshot.
    Returns the path to the saved image, or None if it fails.
    
    Docs: https://stitch.withgoogle.com/docs/mcp/setup
    """
    api_key = os.environ.get("STITCH_API_KEY", "").strip()
    if not api_key:
        print("⚠️  STITCH_API_KEY not found in environment. Skipping Stitch generation.")
        return None

    print(f"🪄  Prompting Stitch API: '{prompt[:60]}...'")

    # Correct endpoint from official docs
    endpoint = "https://stitch.googleapis.com/mcp"
    project_id = "tech-8ytees-shorts"
    
    # 1. Generate screen from text using correct tool name
    create_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "generate_screen_from_text",
            "arguments": {
                "projectId": project_id,
                "prompt": prompt,
                "modelId": "GEMINI_3_FLASH"  # Fast model for automation
            }
        }
    }
    
    # Correct header format from docs
    headers = {
        "X-Goog-Api-Key": api_key,
        "Content-Type": "application/json"
    }

    try:
        # Step 1: Create screen
        response = requests.post(endpoint, json=create_payload, headers=headers, timeout=60)
        
        if response.status_code != 200:
            print(f"⚠️ Stitch API returned status {response.status_code}: {response.text[:200]}")
            return None
            
        data = response.json()
        if "error" in data:
            print(f"❌ Stitch API error: {data['error']}")
            return None
            
        # Parse the response to extract screen resource name
        screen_name = None
        screen_id = None
        try:
            # MCP tools/call response format: {result: {content: [{type: "text", text: ...}]}}
            result = data.get("result", {})
            content = result.get("content", [])
            
            for item in content:
                if item.get("type") == "text":
                    text = item.get("text", "")
                    # The response typically contains the screen resource name
                    # Format: "projects/{projectId}/screens/{screenId}"
                    import re
                    name_match = re.search(r'projects/[^/]+/screens/([a-zA-Z0-9_-]+)', text)
                    if name_match:
                        screen_name = name_match.group(0)
                        screen_id = name_match.group(1)
                        break
                    
                    # Also try parsing as JSON
                    try:
                        parsed = json.loads(text)
                        screen_name = parsed.get("name")
                        if screen_name and "screens/" in screen_name:
                            screen_id = screen_name.split("/screens/")[-1]
                            break
                    except:
                        pass
            
            # Alternative: might be directly in result
            if not screen_name:
                screen_name = result.get("name")
                if screen_name:
                    screen_id = screen_name.split("/screens/")[-1] if "/screens/" in screen_name else None
                
        except Exception as e:
            print(f"⚠️ Could not parse screen name: {e}")
            print(f"Response preview: {json.dumps(data, indent=2)[:500]}")
        
        if not screen_name:
            print("⚠️ No screen created or response format changed.")
            return None
        
        print(f"✅ Screen created: {screen_name}")
        
        # Step 2: Retrieve screen details to get image URL
        # Stitch screens include preview images we can download
        max_attempts = 8
        for attempt in range(max_attempts):
            time.sleep(3)  # Wait for Stitch to render
            
            screen_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "get_screen",
                    "arguments": {
                        "name": screen_name
                    }
                }
            }
            
            screen_response = requests.post(endpoint, json=screen_payload, headers=headers, timeout=60)
            
            if screen_response.status_code == 200:
                screen_data = screen_response.json()
                
                if "error" in screen_data:
                    error_msg = screen_data.get("error", {}).get("message", "Unknown error")
                    if "not found" in error_msg.lower() or attempt < max_attempts - 1:
                        print(f"   ⏳ Waiting for screen to finish rendering... ({attempt + 1}/{max_attempts})")
                        continue
                    else:
                        print(f"❌ Screen fetch error: {error_msg}")
                        return None
                
                # Parse screen details
                screen_result = screen_data.get("result", {})
                screen_content = screen_result.get("content", [])
                
                # Look for image URL or data in the response
                for item in screen_content:
                    if item.get("type") == "image":
                        # Base64 image data
                        img_data = item.get("data")
                        if img_data:
                            img_bytes = base64.b64decode(img_data)
                            with open(output_path, "wb") as f:
                                f.write(img_bytes)
                            print(f"✅ Stitch image saved: {output_path}")
                            return output_path
                    elif item.get("type") == "text":
                        text = item.get("text", "")
                        # Look for preview image URL in JSON
                        try:
                            parsed = json.loads(text)
                            preview_url = (
                                parsed.get("previewImage") or 
                                parsed.get("previewImageUrl") or
                                parsed.get("imageUrl") or
                                parsed.get("preview")
                            )
                            if preview_url and preview_url.startswith("http"):
                                print(f"   📥 Downloading from: {preview_url[:60]}...")
                                img_bytes = requests.get(preview_url, timeout=30).content
                                with open(output_path, "wb") as f:
                                    f.write(img_bytes)
                                print(f"✅ Stitch image saved: {output_path}")
                                return output_path
                        except:
                            # Maybe the text itself is a URL
                            if text.startswith("http"):
                                print(f"   📥 Downloading from URL...")
                                img_bytes = requests.get(text, timeout=30).content
                                with open(output_path, "wb") as f:
                                    f.write(img_bytes)
                                print(f"✅ Stitch image saved: {output_path}")
                                return output_path
                
                # If no image found yet, wait and retry
                if attempt < max_attempts - 1:
                    print(f"   ⏳ No image URL yet, retrying... ({attempt + 1}/{max_attempts})")
                    continue
                else:
                    print(f"⚠️ Screen created but no preview image available after {max_attempts} attempts")
                    print(f"   Response preview: {json.dumps(screen_data, indent=2)[:400]}")
                    return None
            else:
                print(f"⚠️ get_screen returned {screen_response.status_code}: {screen_response.text[:200]}")
                if attempt < max_attempts - 1:
                    continue
                return None
                
    except Exception as e:
        print(f"❌ Stitch API error: {e}")
        import traceback
        traceback.print_exc()
        return None

    return None
