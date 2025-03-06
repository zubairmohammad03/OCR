from flask import Flask, request, jsonify
import requests
import json
import base64
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Get API key from .env file
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Google Gemini API URL
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def encode_image(image_file):
    """Encodes an image to base64 format."""
    return base64.b64encode(image_file.read()).decode("utf-8")

def generate_caption(image_data, prompt):
    """Sends the image and prompt to Google's Gemini API and returns the response."""
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_data
                        }
                    },
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {"responseMimeType": "application/json"}
    }

    response = requests.post(f"{GEMINI_API_URL}?key={GEMINI_API_KEY}", headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        try:
            response_json = response.json()
            return response_json["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return "Unexpected response format"
    else:
        return f"Request failed with status code {response.status_code}: {response.text}"

@app.route('/generate_caption', methods=['POST'])
def generate_captions():
    """API endpoint to generate captions for two uploaded images."""
    if 'image1' not in request.files or 'image2' not in request.files:
        return jsonify({"error": "Both images are required"}), 400

    image1 = request.files['image1']
    image2 = request.files['image2']

    try:
        # Encode images
        image_data1 = encode_image(image1)
        image_data2 = encode_image(image2)

        # Define prompts
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

        # Generate captions
        caption1 = generate_caption(image_data1, prompt1)
        caption2 = generate_caption(image_data2, prompt2)

        return jsonify({"caption1": caption1, "caption2": caption2})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
