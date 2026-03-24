import os
import requests
import time
import json
import base64


def check_stitch_project(project_id: str = "tech-8ytees-shorts") -> bool:
    """
    Quick check if Stitch project exists and API key is valid.
    Returns True if project is accessible, False otherwise.
    """
    api_key = os.environ.get("STITCH_API_KEY", "").strip()
    if not api_key:
        return False
    
    endpoint = "https://stitch.googleapis.com/mcp"
    headers = {
        "X-Goog-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Try to get project details
    payload = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "tools/call",
        "params": {
            "name": "get_project",
            "arguments": {
                "name": f"projects/{project_id}"
            }
        }
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "error" not in data:
                return True
            error_msg = data.get("error", {}).get("message", "")
            if "not found" in error_msg.lower():
                print(f"⚠️  Stitch project '{project_id}' not found.")
                print(f"   Create it at: https://stitch.withgoogle.com/")
                return False
            elif "permission" in error_msg.lower() or "auth" in error_msg.lower():
                print(f"⚠️  Stitch API key invalid or lacks permissions.")
                print(f"   Check your API key at: https://stitch.withgoogle.com/settings")
                return False
    except Exception as e:
        print(f"⚠️  Could not connect to Stitch API: {e}")
    
    return False


def generate_ui_image(prompt: str, output_path: str = "output_ui.jpg") -> str | None:
    """
    Calls the Google Stitch API via MCP to generate a UI / screenshot.
    Returns the path to the saved image, or None if it fails.
    
    Docs: https://stitch.withgoogle.com/docs/mcp/setup
    
    Prerequisites:
    1. STITCH_API_KEY environment variable must be set
    2. Project "tech-8ytees-shorts" must exist in your Stitch account
       (Create it at https://stitch.withgoogle.com/ if needed)
    """
    api_key = os.environ.get("STITCH_API_KEY", "").strip()
    if not api_key:
        print("⚠️  STITCH_API_KEY not found in environment. Skipping Stitch generation.")
        print("   Get your API key at: https://stitch.withgoogle.com/settings")
        return None

    print(f"🪄  Prompting Stitch API: '{prompt[:60]}...'")

    # Correct endpoint from official docs
    endpoint = "https://stitch.googleapis.com/mcp"
    project_id = "tech-8ytees-shorts"
    
    print(f"   Using project: {project_id}")
    
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
            error_info = data.get("error", {})
            error_msg = error_info.get("message", str(error_info))
            print(f"❌ Stitch API error: {error_msg}")
            print(f"   Full error: {json.dumps(error_info, indent=2)}")
            return None
        
        # Debug: Print full response to understand format
        print(f"📋 Stitch response: {json.dumps(data, indent=2)[:800]}")
            
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
            print("⚠️ No screen name found in response.")
            print(f"   Response structure: result keys = {list(result.keys())}")
            print(f"   Content items: {len(content)} items")
            if content:
                print(f"   First content item type: {content[0].get('type') if content else 'N/A'}")
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
