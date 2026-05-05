import os
import requests
import json
import base64

api_key = os.environ.get("GEMINI_API_KEY")
# Using the specific Vertex AI/Cloud endpoint that supports Studio voices
url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"

def generate_studio_audio(text, output_path):
    payload = {
        "input": {"text": text},
        "voice": {
            "languageCode": "en-US", 
            "name": "en-US-Studio-O" # One of Google's highest quality Studio voices
        },
        "audioConfig": {"audioEncoding": "MP3"}
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        audio_content = response.json().get("audioContent")
        with open(output_path, "wb") as out:
            out.write(base64.b64decode(audio_content))
        print(f"SUCCESS: Google Studio audio generated.")
        return True
    else:
        print(f"FAILED: Status {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    # If the user has enabled the API, this will work. 
    # Otherwise, we will know for sure.
    generate_studio_audio("Vav. Hey. Vav.", "static/audio/1.mp3")
