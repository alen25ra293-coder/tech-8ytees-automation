import os
from google import genai
from google.genai import types

def test_imagen():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        api_keys = os.environ.get("GEMINI_API_KEYS", "").split(",")
        if api_keys:
            api_key = api_keys[0].strip()
    
    if not api_key:
        print("No API key")
        return

    try:
        client = genai.Client(api_key=api_key)
        result = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt='A photorealistic image of a Portronics PAT wireless charger on a wooden desk',
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="9:16"
            )
        )
        for i, generated_image in enumerate(result.generated_images):
            with open(f"imagen_test_{i}.jpg", "wb") as f:
                f.write(generated_image.image.image_bytes)
            print(f"Success! Saved image {i}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_imagen()
