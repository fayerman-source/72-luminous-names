import os
from google import genai
import base64

def test_gemini_format_v3():
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    prompt = (
        "Sing the Hebrew letters 'Vav', 'Hey', and 'Vav' in a deep, meditative, and slow chanting style. "
        "Stretch out each syllable. Do not speak. Sing with a melodic, spiritual cadence. "
    )

    try:
        response = client.models.generate_content(
            model='gemini-3.1-flash-tts-preview',
            contents=prompt,
            config={
                'speech_config': {'voice_config': {'prebuilt_voice_config': {'voice_name': 'Aoede'}}}
            }
        )
        
        for i, part in enumerate(response.candidates[0].content.parts):
            if hasattr(part, 'inline_data') and part.inline_data:
                print(f"Part {i} has inline_data.")
                print(f"Mime Type: {part.inline_data.mime_type}")
                with open(f"test_part_{i}.raw", "wb") as f:
                    f.write(part.inline_data.data)
            else:
                print(f"Part {i} is text: {part.text if hasattr(part, 'text') else 'N/A'}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_gemini_format_v3()
