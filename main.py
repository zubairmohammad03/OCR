from flask import Flask, request, jsonify
import requests
import json
import base64
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# Load API Key from Environment Variable for Security
API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

# Configurable Rate Limiting (Default: 10 requests per minute)
RATE_LIMIT = os.getenv("RATE_LIMIT", "10 per minute")

# Initialize Limiter
limiter = Limiter(
    key_func=get_remote_address,  # Limits requests based on client IP
    app=app,
    default_limits=[RATE_LIMIT]  # Use configurable limit from env
)

def generate_caption_from_image(image_data):
    """
    Generates a caption for an uploaded image using Google's Gemini API.

    Args:
        image_data (bytes): The image file in binary format.

    Returns:
        dict: The extracted passport details or an error message.
    """

    # Encode image in base64
    image_base64 = base64.b64encode(image_data).decode("utf-8")

    # Construct the request payload
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    },
                    {"text": '''Caption this image in the following format:
                    Note: Place of Birth and Place of Issue are Indian Places.
                    Note: MRZ always consists of 88 characters; if more or less, adjust the < accordingly.
                    {"Passport Number": "N0830745", "Surname": "DHUMAL", "Given Name": "MANOJ BABRUVHAN", "Nationality": "INDIAN", "Sex": "M", "Date of Birth": "13/09/1982", "Place of Birth": "PUNE, MAHARASHTRA", "Place of Issue": "PUNE", "Date of Issue": "29/06/2015", "Date of Expiry": "28/06/2025", "Type": "P", "MRZ":"The MRZ code in the image"}'''}
                ]
            }
        ],
        "generationConfig": {"responseMimeType": "application/json"}
    }

    # Send request to Gemini API
    response = requests.post(GEMINI_URL, headers={'Content-Type': 'application/json'}, data=json.dumps(data))

    if response.status_code == 200:
        try:
            response_json = response.json()
            return response_json["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return {"error": "Unexpected response format"}
    else:
        return {"error": f"Request failed with status code {response.status_code}: {response.text}"}


@app.route("/extract_passport", methods=["POST"])
@limiter.limit(RATE_LIMIT)  # Apply rate limit
def extract_passport():
    """
    API Endpoint to extract passport details from an uploaded image.
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files["image"]
    image_data = image_file.read()

    result = generate_caption_from_image(image_data)
    return jsonify(result)


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to Passport OCR API"})


@app.errorhandler(429)
def ratelimit_handler(e):
    """Handles rate limit errors."""
    return jsonify(error="Too many requests. Please try again later."), 429


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
