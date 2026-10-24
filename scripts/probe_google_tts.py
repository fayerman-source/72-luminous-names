import os
import requests
import json
import base64

api_key = os.environ.get("GEMINI_API_KEY")
url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"

payload = {
    "input": {"text": "והו"},
    "voice": {"languageCode": "he-IL", "name": "he-IL-Neural2-A"},
    "audioConfig": {"audioEncoding": "MP3"}
}

response = requests.post(url, json=payload)

if response.status_code == 200:
    audio_content = response.json().get("audioContent")
    with open("static/audio/1.mp3", "wb") as out:
        out.write(base64.b64decode(audio_content))
    print("SUCCESS: High-quality Google Neural2 audio generated.")
else:
    print(f"FAILED: Status {response.status_code}")
    print(response.text)
