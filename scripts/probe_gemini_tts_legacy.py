import os
import google.generativeai as genai
import sys

def generate_gemini_audio(hebrew_name, transliteration, output_path):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment.")
        return False
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = (
        f"You are a professional meditation guide. "
        f"Please speak the individual Hebrew letters for the name '{hebrew_name}' clearly and slowly. "
        f"The letters are: {transliteration}. "
        f"Pronounce each letter separately with a small pause between them. "
        f"Output ONLY the audio of you speaking these letters. "
        f"Do not include any background music or introductory text."
    )

    try:
        # Requesting audio output from Gemini 1.5 Flash
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "audio/wav"}
        )
        
        # Check if audio was returned in the response parts
        audio_part = next((part for part in response.candidates[0].content.parts if part.inline_data), None)
        
        if audio_part:
            with open(output_path, "wb") as f:
                f.write(audio_part.inline_data.data)
            print(f"SUCCESS: Gemini-native audio generated for {hebrew_name}.")
            return True
        else:
            print("Error: No audio data returned by Gemini.")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Exception during Gemini audio generation: {str(e)}")
        return False

if __name__ == "__main__":
    generate_gemini_audio("והו", "Vav, Hey, Vav", "static/audio/1.mp3")
