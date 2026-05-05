import os
from google import genai
import base64
import subprocess

def test_gemini_male_singing():
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    prompt = (
        "Sing the Hebrew letters 'Vav', 'Hey', and 'Vav' in a deep, meditative, and slow chanting style. "
        "Stretch out each syllable. Do not speak. Sing with a melodic, spiritual cadence. "
    )

    try:
        # Using the "Charon" voice which is a deep male voice
        response = client.models.generate_content(
            model='gemini-3.1-flash-tts-preview',
            contents=prompt,
            config={
                'speech_config': {'voice_config': {'prebuilt_voice_config': {'voice_name': 'Charon'}}}
            }
        )
        
        found_audio = False
        for i, part in enumerate(response.candidates[0].content.parts):
            if hasattr(part, 'inline_data') and part.inline_data:
                raw_path = "test_male.raw"
                with open(raw_path, "wb") as f:
                    f.write(part.inline_data.data)
                
                # Convert to MP3
                subprocess.run([
                    "ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1", 
                    "-i", raw_path, "-b:a", "128k", "static/audio/1.mp3"
                ], capture_output=True)
                
                print("SUCCESS: Gemini male 'singing' audio captured and converted.")
                found_audio = True
                break
        
        if not found_audio:
            print("No audio data returned.")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_gemini_male_singing()
