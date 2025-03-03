import requests
import json
import base64

def generate_caption_from_local_image(image_path, api_key):
    """
    Generates a caption for a local image using Google's Gemini API.

    Args:
        image_path (str): The path to the local image file.
        api_key (str): The Gemini API key.

    Returns:
        str: The generated caption or an error message.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}

    # Read and encode the image in base64
    try:
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        return "Error: Image file not found."
    except Exception as e:
        return f"Error reading image: {str(e)}"

    # Construct the request payload in the correct format
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_data
                        }
                    },
                    {"text": '''Caption this image. in the following format 
                     Note: Place of Birth and place of Issue are Indian Places
                     Note: MRZ always consists of 88 characters, if more or less, please adjust the < accordingly
                     {"Passport Number": "N0830745", "Surname": "DHUMAL", "Given Name": "MANOJ BABRUVHAN", "Nationality": "INDIAN", "Sex": "M", "Date of Birth": "13/09/1982", "Place of Birth": "PUNE, MAHARASHTRA", "Place of Issue": "PUNE", "Date of Issue": "29/06/2015", "Date of Expiry": "28/06/2025", "Type": "P", "MRZ":"The MRZ code in the image"}'''}
                ]
            }
        ],
        "generationConfig": {"responseMimeType": "application/json"}
    }

    # Send request to Gemini API
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        try:
            response_json = response.json()
            return response_json["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return "Unexpected response format"
    else:
        return f"Request failed with status code {response.status_code}: {response.text}"

# Example usage
api_key = "AIzaSyAIASQ9IVxHqwRTXcttaLSCNqGb2PVE_8k"  # Replace with your actual API key
image_path = "OCR\Workspace\Sarabjot Singh 13-4-96 (Y4841462)-1.jpg"  # Replace with the path to your image

caption = generate_caption_from_local_image(image_path, api_key)
print(caption)
