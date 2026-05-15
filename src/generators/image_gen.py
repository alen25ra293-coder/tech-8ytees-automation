import os
import uuid
from google import genai
from google.genai import types

def generate_product_image(product_name: str, topic: str, output_path: str = None) -> str:
    """
    Generates a high-quality product image using Gemini Imagen 3.0 API.
    Returns the file path of the generated image.
    """
    api_key = os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY", "")
    if "," in api_key:
        api_key = api_key.split(",")[0].strip()
        
    if not api_key:
        print("⚠️ No Gemini API key found for image generation.")
        return None

    if not output_path:
        os.makedirs("assets", exist_ok=True)
        output_path = f"assets/gen_img_{uuid.uuid4().hex[:8]}.jpg"

    prompt = f"A photorealistic, highly detailed 4k image of a {product_name or topic}. The product is shown clearly on a clean modern desk setup, cinematic lighting, shallow depth of field, tech aesthetic, dynamic angle."

    try:
        print(f"🎨 Generating image for: {product_name or topic}...")
        client = genai.Client(api_key=api_key)
        result = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="9:16"
            )
        )
        
        if result.generated_images:
            generated_image = result.generated_images[0]
            with open(output_path, "wb") as f:
                f.write(generated_image.image.image_bytes)
            print(f"   ✅ Generated image saved to {output_path}")
            return output_path
        else:
            print("   ⚠️ Image generation returned no images.")
            return None
            
    except Exception as e:
        print(f"   ⚠️ Image generation failed: {e}")
        return None
