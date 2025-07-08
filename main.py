from flask import Flask, request, jsonify
import requests
import json
import base64
import os
import time

app = Flask(__name__)

# Use secure environment variable for API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError("Missing GEMINI_API_KEY in environment variables")

# Model fallbacks in order
GEMINI_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-pro-latest",
    "gemini-2.5-flash-preview-04-17"
]

def encode_image(image_file):
    """Encodes an image to base64 format."""
    return base64.b64encode(image_file.read()).decode("utf-8")

def generate_caption(image_data, prompt):
    """Retries Gemini API call with exponential backoff and fallback models."""
    headers = {"Content-Type": "application/json"}

    for model in GEMINI_MODELS:
        for attempt in range(5):  # max 5 retries
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": image_data
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {"responseMimeType": "application/json"}
            }

            try:
                response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=40)

                if response.status_code == 200:
                    response_json = response.json()
                    return response_json["candidates"][0]["content"]["parts"][0]["text"]
                elif response.status_code == 503:
                    wait_time = 2 ** attempt
                    print(f"[Gemini] Model overloaded. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"[Gemini] Error {response.status_code}: {response.text}")
                    return f"Request failed with status code {response.status_code}: {response.text}"

            except Exception as e:
                print(f"[Gemini] Exception: {str(e)}")
                time.sleep(2 ** attempt)

    return "All models failed after retries. Gemini is currently unavailable."

@app.route('/generate_caption', methods=['POST'])
def generate_captions():
    """API endpoint to generate captions for two uploaded images."""

    if 'image1' not in request.files or 'image2' not in request.files:
        return jsonify({"error": "Both images are required"}), 400

    image1 = request.files['image1']
    image2 = request.files['image2']

    if image1.filename == "" or image2.filename == "":
        return jsonify({"error": "Both images must be selected"}), 400

    try:
        image_data1 = encode_image(image1)
        image_data2 = encode_image(image2)

        # Prompts
        prompt1 = '''Caption this image. in the following format:
Note: Place of Birth and Place of Issue are Indian Places.
Note: MRZ always consists of 88 characters. If more or less, please adjust the < accordingly.
{"Passport Number": "N0830745", "Surname": "DHUMAL", "Given Name": "MANOJ BABRUVHAN",
"Nationality": "INDIAN", "Sex": "M", "Date of Birth": "13/09/1982",
"Place of Birth": "PUNE, MAHARASHTRA", "Place of Issue": "PUNE",
"Date of Issue": "29/06/2015", "Date of Expiry": "28/06/2025",
"Type": "P", "MRZ": "The MRZ code in the image"}'''

        prompt2 = '''Caption this image. in the following format:
Note: Old Passport Issue Place is always an Indian place.
{"Name of Father/Legal Guardian": "MAHASAYAN KAIDAVALPIL THANKAPPAN",
"Name of Mother": "USHA MAHASAYAN", "Name of Spouse": "SREEJA SIVANANDAN",
"Address": "108 G SHAKTIKHAND 3 INDIRAPURAM, GHAZIABAD PIN:201014, UTTAR PRADESH, INDIA",
"FileNo": "621071323803817", "Old Passport No": "J7508785",
"Old Passport Issue Date": "10/06/2011", "Old Passport Issue Place": "GHAZIABAD"}'''

        caption1 = generate_caption(image_data1, prompt1)
        caption2 = generate_caption(image_data2, prompt2)

        return jsonify({"caption1": caption1, "caption2": caption2})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to Passport OCR API (Cloud Run)"})

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)
