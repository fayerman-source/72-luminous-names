import os
from google import genai
import base64

def test_gemini_singing():
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    # We use a prompt that explicitly asks for CHANTING/SINGING
    prompt = (
        "Sing the Hebrew letters 'Vav', 'Hey', and 'Vav' in a deep, meditative, and slow chanting style. "
        "Stretch out each syllable. Do not speak. Sing with a melodic, spiritual cadence. "
        "High quality audio output required."
    )

    try:
        # Using the specific TTS-optimized model
        response = client.models.generate_content(
            model='gemini-3.1-flash-tts-preview',
            contents=prompt,
            config={
                'speech_config': {'voice_config': {'prebuilt_voice_config': {'voice_name': 'Aoede'}}}
            }
        )
        
        # Check for audio in parts
        found_audio = False
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                with open("static/audio/1.mp3", "wb") as f:
                    f.write(part.inline_data.data)
                print("SUCCESS: Gemini 'singing' audio captured.")
                found_audio = True
                break
        
        if not found_audio:
            print("No audio data returned. Response text below:")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_gemini_singing()
