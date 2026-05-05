import os
import subprocess
import tempfile
from google import genai

# The traditional 72 Names of God with their spiritual intentions
NAMES = [
    {"id": 1, "name": "והו", "transliteration": "Vav Hey Vav", "meaning": "Time Travel / Return to Creation", "theme": "Time Travel"},
    {"id": 2, "name": "ילי", "transliteration": "Yud Lamed Yud", "meaning": "Recapturing the Sparks", "theme": "Recapturing Sparks"},
    {"id": 3, "name": "סית", "transliteration": "Samech Yud Tav", "meaning": "Miracle Making", "theme": "Miracle Making"},
    {"id": 4, "name": "עלם", "transliteration": "Ayin Lamed Mem", "meaning": "Eliminating Negative Thoughts", "theme": "Negative Thoughts"},
    {"id": 5, "name": "מהש", "transliteration": "Mem Hey Shin", "meaning": "Healing", "theme": "Healing"},
    {"id": 6, "name": "ללה", "transliteration": "Lamed Lamed Hey", "meaning": "Dream State", "theme": "Dream State"},
    {"id": 7, "name": "אכא", "transliteration": "Aleph Khaf Aleph", "meaning": "DNA of the Soul", "theme": "Soul DNA"},
    {"id": 8, "name": "כהת", "transliteration": "Khaf Hey Tav", "meaning": "Defusing Negative Energy", "theme": "Negative Energy"},
    {"id": 9, "name": "הזי", "transliteration": "Hey Zayin Yud", "meaning": "Angelic Influences", "theme": "Angels"},
    {"id": 10, "name": "אלד", "transliteration": "Aleph Lamed Dalet", "meaning": "Protection from the Evil Eye", "theme": "Protection"},
    {"id": 11, "name": "לאו", "transliteration": "Lamed Aleph Vav", "meaning": "Banishing the Remnants of Evil", "theme": "Banish Evil"},
    {"id": 12, "name": "ההע", "transliteration": "Hey Hey Ayin", "meaning": "Unconditional Love", "theme": "Love"},
    {"id": 13, "name": "יזל", "transliteration": "Yud Zayin Lamed", "meaning": "Heaven on Earth", "theme": "Heaven"},
    {"id": 14, "name": "מבה", "transliteration": "Mem Bet Hey", "meaning": "Farewell to Arms", "theme": "Peace"},
    {"id": 15, "name": "הרי", "transliteration": "Hey Resh Yud", "meaning": "Long-Range Vision", "theme": "Vision"},
    {"id": 16, "name": "הקם", "transliteration": "Hey Kof Mem", "meaning": "Dumping Depression", "theme": "Dumping Depression"},
    {"id": 17, "name": "לאו", "transliteration": "Lamed Aleph Vav", "meaning": "Great Escape", "theme": "Great Escape"},
    {"id": 18, "name": "כלי", "transliteration": "Khaf Lamed Yud", "meaning": "Fertility", "theme": "Fertility"},
    {"id": 19, "name": "לוו", "transliteration": "Lamed Vav Vav", "meaning": "Dialing God", "theme": "Dialing God"},
    {"id": 20, "name": "פהל", "transliteration": "Pe Hey Lamed", "meaning": "Victory over Addictions", "theme": "Victory"},
    {"id": 21, "name": "נלך", "transliteration": "Nun Lamed Khaf", "meaning": "Eradicating Plague", "theme": "Eradicate Plague"},
    {"id": 22, "name": "ייי", "transliteration": "Yud Yud Yud", "meaning": "Stop Fatal Attraction", "theme": "Fatal Attraction"},
    {"id": 23, "name": "מלה", "transliteration": "Mem Lamed Hey", "meaning": "Sharing the Flame", "theme": "Sharing"},
    {"id": 24, "name": "חהו", "transliteration": "Chet Hey Vav", "meaning": "Jealousy", "theme": "Jealousy"},
    {"id": 25, "name": "נתה", "transliteration": "Nun Tav Hey", "meaning": "Speak Your Mind", "theme": "Speak Your Mind"},
    {"id": 26, "name": "האא", "transliteration": "Hey Aleph Aleph", "meaning": "Order from Chaos", "theme": "Order"},
    {"id": 27, "name": "ירת", "transliteration": "Yud Resh Tav", "meaning": "Silent Partner", "theme": "Silent Partner"},
    {"id": 28, "name": "שאה", "transliteration": "Shin Aleph Hey", "meaning": "Soul Mate", "theme": "Soul Mate"},
    {"id": 29, "name": "ריי", "transliteration": "Resh Yud Yud", "meaning": "Removing Hatred", "theme": "Remove Hatred"},
    {"id": 30, "name": "אום", "transliteration": "Aleph Vav Mem", "meaning": "Building Bridges", "theme": "Building Bridges"},
    {"id": 31, "name": "לכב", "transliteration": "Lamed Khaf Bet", "meaning": "Finish What You Start", "theme": "Finish"},
    {"id": 32, "name": "ושר", "transliteration": "Vav Shin Resh", "meaning": "Memories", "theme": "Memories"},
    {"id": 33, "name": "יחו", "transliteration": "Yud Chet Vav", "meaning": "Revealing the Dark Side", "theme": "Dark Side"},
    {"id": 34, "name": "להח", "transliteration": "Lamed Hey Chet", "meaning": "Forget Thyself", "theme": "Forget Thyself"},
    {"id": 35, "name": "כוק", "transliteration": "Khaf Vav Kof", "meaning": "Sexual Energy", "theme": "Sexual Energy"},
    {"id": 36, "name": "מנד", "transliteration": "Mem Nun Dalet", "meaning": "Fearless", "theme": "Fearless"},
    {"id": 37, "name": "אני", "transliteration": "Aleph Nun Yud", "meaning": "The Big Picture", "theme": "Big Picture"},
    {"id": 38, "name": "חעם", "transliteration": "Chet Ayin Mem", "meaning": "Circuitry", "theme": "Circuitry"},
    {"id": 39, "name": "רהע", "transliteration": "Resh Hey Ayin", "meaning": "Diamond in the Rough", "theme": "Diamond"},
    {"id": 40, "name": "ייז", "transliteration": "Yud Yud Zayin", "meaning": "Speaking the Right Words", "theme": "Right Words"},
    {"id": 41, "name": "ההה", "transliteration": "Hey Hey Hey", "meaning": "Self-Esteem", "theme": "Self-Esteem"},
    {"id": 42, "name": "מיכ", "transliteration": "Mem Yud Khaf", "meaning": "Revealing the Concealed", "theme": "Revealing"},
    {"id": 43, "name": "וול", "transliteration": "Vav Vav Lamed", "meaning": "Defying Gravity", "theme": "Defying Gravity"},
    {"id": 44, "name": "ילה", "transliteration": "Yud Lamed Hey", "meaning": "Sweetening Judgment", "theme": "Judgment"},
    {"id": 45, "name": "סאל", "transliteration": "Samech Aleph Lamed", "meaning": "The Power of Prosperity", "theme": "Prosperity"},
    {"id": 46, "name": "ערי", "transliteration": "Ayin Resh Yud", "meaning": "Absolute Certainty", "theme": "Certainty"},
    {"id": 47, "name": "עשל", "transliteration": "Ayin Shin Lamed", "meaning": "Global Transformation", "theme": "Transformation"},
    {"id": 48, "name": "מיה", "transliteration": "Mem Yud Hey", "meaning": "Unity", "theme": "Unity"},
    {"id": 49, "name": "והו", "transliteration": "Vav Hey Vav", "meaning": "Happiness", "theme": "Happiness"},
    {"id": 50, "name": "דני", "transliteration": "Dalet Nun Yud", "meaning": "Enough is Enough", "theme": "Enough"},
    {"id": 51, "name": "החש", "transliteration": "Hey Chet Shin", "meaning": "No Guilt", "theme": "No Guilt"},
    {"id": 52, "name": "עמם", "transliteration": "Ayin Mem Mem", "meaning": "Passion", "theme": "Passion"},
    {"id": 53, "name": "ננא", "transliteration": "Nun Nun Aleph", "meaning": "No Agenda", "theme": "No Agenda"},
    {"id": 54, "name": "נית", "transliteration": "Nun Yud Tav", "meaning": "Death of Death", "theme": "Death of Death"},
    {"id": 55, "name": "מבה", "transliteration": "Mem Bet Hey", "meaning": "Thought into Action", "theme": "Action"},
    {"id": 56, "name": "פוי", "transliteration": "Pe Vav Yud", "meaning": "Dispelling Anger", "theme": "Dispel Anger"},
    {"id": 57, "name": "נמם", "transliteration": "Nun Mem Mem", "meaning": "Listening to Your Soul", "theme": "Soul Listening"},
    {"id": 58, "name": "ייל", "transliteration": "Yud Yud Lamed", "meaning": "Letting Go", "theme": "Letting Go"},
    {"id": 59, "name": "הרח", "transliteration": "Hey Resh Chet", "meaning": "Umbilical Cord", "theme": "Umbilical Cord"},
    {"id": 60, "name": "מצר", "transliteration": "Mem Tzadi Resh", "meaning": "Freedom", "theme": "Freedom"},
    {"id": 61, "name": "ומב", "transliteration": "Vav Mem Bet", "meaning": "Water", "theme": "Water"},
    {"id": 62, "name": "יהה", "transliteration": "Yud Hey Hey", "meaning": "Parent-Teacher", "theme": "Parent-Teacher"},
    {"id": 63, "name": "ענו", "transliteration": "Ayin Nun Vav", "meaning": "Appreciation", "theme": "Appreciation"},
    {"id": 64, "name": "מחי", "transliteration": "Mem Chet Yud", "meaning": "Casting Yourself in a Favorable Light", "theme": "Favorable Light"},
    {"id": 65, "name": "דמב", "transliteration": "Dalet Mem Bet", "meaning": "Fear of God", "theme": "Fear of God"},
    {"id": 66, "name": "מנק", "transliteration": "Mem Nun Kof", "meaning": "Accountability", "theme": "Accountability"},
    {"id": 67, "name": "איע", "transliteration": "Aleph Yud Ayin", "meaning": "Great Expectations", "theme": "Great Expectations"},
    {"id": 68, "name": "חבו", "transliteration": "Chet Bet Vav", "meaning": "Contacting Departed Souls", "theme": "Contacting Souls"},
    {"id": 69, "name": "ראה", "transliteration": "Resh Aleph Hey", "meaning": "Lost and Found", "theme": "Lost and Found"},
    {"id": 70, "name": "יבם", "transliteration": "Yud Bet Mem", "meaning": "Recognizing Design Beneath Disorder", "theme": "Recognizing Design"},
    {"id": 71, "name": "היי", "transliteration": "Hey Yud Yud", "meaning": "Prophecy and Parallel Universes", "theme": "Prophecy"},
    {"id": 72, "name": "מום", "transliteration": "Mem Vav Mem", "meaning": "Spiritual Cleansing", "theme": "Cleansing"},
]

def generate_audio(name_data, output_dir, client):
    transliteration = name_data["transliteration"]
    output_file = os.path.join(output_dir, f"{name_data['id']}.mp3")

    prompt = (
        f"Sing the Hebrew letters '{transliteration}' in a deep, meditative, and slow chanting style. "
        "Stretch out each syllable. Do not speak. Sing with a melodic, spiritual cadence. "
    )

    try:
        # Generate meditative chanting using Gemini 3.1 Flash TTS Preview
        response = client.models.generate_content(
            model='gemini-3.1-flash-tts-preview',
            contents=prompt,
            config={
                'speech_config': {'voice_config': {'prebuilt_voice_config': {'voice_name': 'Charon'}}}
            }
        )
        
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                # Capture raw audio data (PCM Linear 16, 24kHz)
                with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as tmp:
                    tmp.write(part.inline_data.data)
                    tmp_path = tmp.name
                
                # Convert raw PCM to high-quality MP3 using ffmpeg
                subprocess.run([
                    "ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1", 
                    "-i", tmp_path, "-b:a", "128k", output_file
                ], capture_output=True)
                
                os.unlink(tmp_path)
                print(f"Generated: {output_file} (Chanted: {transliteration})")
                return True
        
        print(f"Error: No audio data returned for {transliteration}")
        return False
        
    except Exception as e:
        print(f"Exception for {transliteration}: {str(e)}")
        return False


if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is required.")
        exit(1)

    client = genai.Client(api_key=api_key)
    output_dir = "static/audio"
    os.makedirs(output_dir, exist_ok=True)

    print(f"Starting generation of 72 Luminous Names with Gemini 'Charon' voice...")
    
    success_count = 0
    for name in NAMES:
        if generate_audio(name, output_dir, client):
            success_count += 1

    print(f"\n✓ Successfully generated {success_count}/72 high-quality meditative audio files.")
    print(f"Location: {output_dir}/")
