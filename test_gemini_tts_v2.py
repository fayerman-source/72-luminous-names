import os
from google import genai
import base64

def generate_gemini_audio(hebrew_name, transliteration, output_path):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found.")
        return False
    
    client = genai.Client(api_key=api_key)
    
    prompt = (
        f"You are a professional meditation guide. "
        f"Please speak the individual Hebrew letters for the name '{hebrew_name}' clearly, slowly, and with space between them. "
        f"The letters to pronounce are: {transliteration}. "
        f"Pronounce each one separately. "
        f"Example: '{transliteration[0]}... {transliteration[1]}... {transliteration[2]}'."
    )

    try:
        # Use the Multimodal Live API style or GenerateContent with speech config
        # Note: In the new SDK, we use speech_generation_config for audio output
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config={
                'speech_config': {'voice_config': {'prebuilt_voice_config': {'voice_name': 'Aoede'}}}
            }
        )
        
        # In the new SDK, audio is returned in the response if configured
        # If not directly returned as a file, we may need to use the Live API or wait for full feature parity
        # For now, let's try to get the audio from the response parts
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data'):
                 with open(output_path, "wb") as f:
                     f.write(part.inline_data.data)
                 print(f"SUCCESS: Gemini audio generated for {hebrew_name}.")
                 return True
        
        print("No audio data found in response.")
        print(f"Response text: {response.text}")
        return False

    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    generate_gemini_audio("והו", "Vav, Hey, Vav", "static/audio/1.mp3")
