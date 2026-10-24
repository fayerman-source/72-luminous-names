import os
import requests
import sys

api_key = os.environ.get("ELEVENLABS_API_KEY")
voice_id = "SAz9YHcvj6GT2YYXdXww" # River - Relaxed
url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

payload = {
    "text": "ו ה ו", # Adding spaces to help with letter-by-letter pronunciation
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.75
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
    print("SUCCESS: Ultra-high quality ElevenLabs audio generated for Name #1.")
else:
    print(f"FAILED: Status {response.status_code}")
    print(response.text)
