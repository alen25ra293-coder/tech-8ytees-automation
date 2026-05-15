import os
import google.generativeai as genai

def test_imagen():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        api_keys = os.environ.get("GEMINI_API_KEYS", "").split(",")
        if api_keys:
            api_key = api_keys[0].strip()
    
    if not api_key:
        print("No API key")
        return

    genai.configure(api_key=api_key)
    try:
        model = genai.ImageGenerationModel("imagen-3.0-generate-001")
        result = model.generate_images(
            prompt="A photorealistic image of a Portronics PAT wireless charger on a wooden desk",
            number_of_images=1,
        )
        print("Success!", result)
    except AttributeError:
        # maybe not in this SDK version
        print("No ImageGenerationModel in this SDK version.")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_imagen()
