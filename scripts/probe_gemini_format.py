import os
from google import genai
import base64

def test_gemini_format():
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    prompt = "Speak the word 'OM' slowly and clearly."

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash', # Trying 2.0 Flash as it's more stable for native audio
            contents=prompt,
            config={
                'speech_config': {'voice_config': {'prebuilt_voice_config': {'voice_name': 'Aoede'}}}
            }
        )
        
        for i, part in enumerate(response.candidates[0].content.parts):
            if hasattr(part, 'inline_data') and part.inline_data:
                print(f"Part {i} has inline_data.")
                print(f"Mime Type: {part.inline_data.mime_type}")
                with open(f"test_part_{i}.bin", "wb") as f:
                    f.write(part.inline_data.data)
            else:
                print(f"Part {i} is text: {part.text}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_gemini_format()
