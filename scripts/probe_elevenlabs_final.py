import os
import requests

api_key = os.environ.get("ELEVENLABS_API_KEY")
voice_id = "JBFqnCBsd6RMkjVDRZzb" # George - Warm & Clear
url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

payload = {
    "text": "Vav. Hey. Vav.",
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
        "stability": 0.8,
        "similarity_boost": 0.8
    }
}

headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": api_key
}

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 200:
    with open("static/audio/1.mp3", "wb") as f:
        f.write(response.content)
    print("SUCCESS: Clear, three-letter pronunciation generated.")
else:
    print(f"FAILED: Status {response.status_code}")
