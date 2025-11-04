import base64
import requests

def call_mistral_ocr(api_key, image_path):
    """
    Calls Mistral OCR API with base64 encoded image.
    """

    model="mistral-ocr-2505"

    # Encode image to Base64
    with open(image_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")

    url = "https://api.mistral.ai/v1/ocr"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "document": {
            "type": "image_url",
            "image_url": f"data:image/png;base64,{img_base64}"
        },
        "include_image_base64": False  # Set True only if you want the image back in response
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
