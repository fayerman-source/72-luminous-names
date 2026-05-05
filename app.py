from flask import Flask, render_template, request, redirect, url_for, session, flash
import os

from datetime import timedelta

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY environment variable is required.")

# Session configuration for better persistence
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
)


def env_flag_enabled(name):
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}

NAMES = [
    {"id": 1, "name": "והו", "transliteration": "Vav Hey Vav", "meaning": "Time Travel / Return to Creation", "theme": "Time Travel", "duration": 10},
    {"id": 2, "name": "ילי", "transliteration": "Yud Lamed Yud", "meaning": "Recapturing the Sparks", "theme": "Recapturing Sparks", "duration": 12},
    {"id": 3, "name": "סית", "transliteration": "Samech Yud Tav", "meaning": "Miracle Making", "theme": "Miracle Making", "duration": 15},
    {"id": 4, "name": "עלם", "transliteration": "Ayin Lamed Mem", "meaning": "Eliminating Negative Thoughts", "theme": "Negative Thoughts", "duration": 10},
    {"id": 5, "name": "מהש", "transliteration": "Mem Hey Shin", "meaning": "Healing", "theme": "Healing", "duration": 12},
    {"id": 6, "name": "ללה", "transliteration": "Lamed Lamed Hey", "meaning": "Dream State", "theme": "Dream State", "duration": 15},
    {"id": 7, "name": "אכא", "transliteration": "Aleph Khaf Aleph", "meaning": "DNA of the Soul", "theme": "Soul DNA", "duration": 10},
    {"id": 8, "name": "כהת", "transliteration": "Khaf Hey Tav", "meaning": "Defusing Negative Energy", "theme": "Negative Energy", "duration": 12},
    {"id": 9, "name": "הזי", "transliteration": "Hey Zayin Yud", "meaning": "Angelic Influences", "theme": "Angels", "duration": 15},
    {"id": 10, "name": "אלד", "transliteration": "Aleph Lamed Dalet", "meaning": "Protection from the Evil Eye", "theme": "Protection", "duration": 10},
    {"id": 11, "name": "לאו", "transliteration": "Lamed Aleph Vav", "meaning": "Banishing the Remnants of Evil", "theme": "Banish Evil", "duration": 12},
    {"id": 12, "name": "ההע", "transliteration": "Hey Hey Ayin", "meaning": "Unconditional Love", "theme": "Love", "duration": 15},
    {"id": 13, "name": "יזל", "transliteration": "Yud Zayin Lamed", "meaning": "Heaven on Earth", "theme": "Heaven", "duration": 10},
    {"id": 14, "name": "מבה", "transliteration": "Mem Bet Hey", "meaning": "Farewell to Arms", "theme": "Peace", "duration": 12},
    {"id": 15, "name": "הרי", "transliteration": "Hey Resh Yud", "meaning": "Long-Range Vision", "theme": "Vision", "duration": 15},
    {"id": 16, "name": "הקם", "transliteration": "Hey Kof Mem", "meaning": "Dumping Depression", "theme": "Dumping Depression", "duration": 10},
    {"id": 17, "name": "לאו", "transliteration": "Lamed Aleph Vav", "meaning": "Great Escape", "theme": "Great Escape", "duration": 12},
    {"id": 18, "name": "כלי", "transliteration": "Khaf Lamed Yud", "meaning": "Fertility", "theme": "Fertility", "duration": 15},
    {"id": 19, "name": "לוו", "transliteration": "Lamed Vav Vav", "meaning": "Dialing God", "theme": "Dialing God", "duration": 10},
    {"id": 20, "name": "פהל", "transliteration": "Pe Hey Lamed", "meaning": "Victory over Addictions", "theme": "Victory", "duration": 12},
    {"id": 21, "name": "נלך", "transliteration": "Nun Lamed Khaf", "meaning": "Eradicating Plague", "theme": "Eradicate Plague", "duration": 15},
    {"id": 22, "name": "ייי", "transliteration": "Yud Yud Yud", "meaning": "Stop Fatal Attraction", "theme": "Fatal Attraction", "duration": 10},
    {"id": 23, "name": "מלה", "transliteration": "Mem Lamed Hey", "meaning": "Sharing the Flame", "theme": "Sharing", "duration": 12},
    {"id": 24, "name": "חהו", "transliteration": "Chet Hey Vav", "meaning": "Jealousy", "theme": "Jealousy", "duration": 15},
    {"id": 25, "name": "נתה", "transliteration": "Nun Tav Hey", "meaning": "Speak Your Mind", "theme": "Speak Your Mind", "duration": 10},
    {"id": 26, "name": "האא", "transliteration": "Hey Aleph Aleph", "meaning": "Order from Chaos", "theme": "Order", "duration": 12},
    {"id": 27, "name": "ירת", "transliteration": "Yud Resh Tav", "meaning": "Silent Partner", "theme": "Silent Partner", "duration": 15},
    {"id": 28, "name": "שאה", "transliteration": "Shin Aleph Hey", "meaning": "Soul Mate", "theme": "Soul Mate", "duration": 10},
    {"id": 29, "name": "ריי", "transliteration": "Resh Yud Yud", "meaning": "Removing Hatred", "theme": "Remove Hatred", "duration": 12},
    {"id": 30, "name": "אום", "transliteration": "Aleph Vav Mem", "meaning": "Building Bridges", "theme": "Building Bridges", "duration": 15},
    {"id": 31, "name": "לכב", "transliteration": "Lamed Khaf Bet", "meaning": "Finish What You Start", "theme": "Finish", "duration": 10},
    {"id": 32, "name": "ושר", "transliteration": "Vav Shin Resh", "meaning": "Memories", "theme": "Memories", "duration": 12},
    {"id": 33, "name": "יחו", "transliteration": "Yud Chet Vav", "meaning": "Revealing the Dark Side", "theme": "Dark Side", "duration": 15},
    {"id": 34, "name": "להח", "transliteration": "Lamed Hey Chet", "meaning": "Forget Thyself", "theme": "Forget Thyself", "duration": 10},
    {"id": 35, "name": "כוק", "transliteration": "Khaf Vav Kof", "meaning": "Sexual Energy", "theme": "Sexual Energy", "duration": 12},
    {"id": 36, "name": "מנד", "transliteration": "Mem Nun Dalet", "meaning": "Fearless", "theme": "Fearless", "duration": 15},
    {"id": 37, "name": "אני", "transliteration": "Aleph Nun Yud", "meaning": "The Big Picture", "theme": "Big Picture", "duration": 10},
    {"id": 38, "name": "חעם", "transliteration": "Chet Ayin Mem", "meaning": "Circuitry", "theme": "Circuitry", "duration": 12},
    {"id": 39, "name": "רהע", "transliteration": "Resh Hey Ayin", "meaning": "Diamond in the Rough", "theme": "Diamond", "duration": 15},
    {"id": 40, "name": "ייז", "transliteration": "Yud Yud Zayin", "meaning": "Speaking the Right Words", "theme": "Right Words", "duration": 10},
    {"id": 41, "name": "ההה", "transliteration": "Hey Hey Hey", "meaning": "Self-Esteem", "theme": "Self-Esteem", "duration": 12},
    {"id": 42, "name": "מיכ", "transliteration": "Mem Yud Khaf", "meaning": "Revealing the Concealed", "theme": "Revealing", "duration": 15},
    {"id": 43, "name": "וול", "transliteration": "Vav Vav Lamed", "meaning": "Defying Gravity", "theme": "Defying Gravity", "duration": 10},
    {"id": 44, "name": "ילה", "transliteration": "Yud Lamed Hey", "meaning": "Sweetening Judgment", "theme": "Judgment", "duration": 12},
    {"id": 45, "name": "סאל", "transliteration": "Samech Aleph Lamed", "meaning": "The Power of Prosperity", "theme": "Prosperity", "duration": 15},
    {"id": 46, "name": "ערי", "transliteration": "Ayin Resh Yud", "meaning": "Absolute Certainty", "theme": "Certainty", "duration": 10},
    {"id": 47, "name": "עשל", "transliteration": "Ayin Shin Lamed", "meaning": "Global Transformation", "theme": "Transformation", "duration": 12},
    {"id": 48, "name": "מיה", "transliteration": "Mem Yud Hey", "meaning": "Unity", "theme": "Unity", "duration": 15},
    {"id": 49, "name": "והו", "transliteration": "Vav Hey Vav", "meaning": "Happiness", "theme": "Happiness", "duration": 10},
    {"id": 50, "name": "דני", "transliteration": "Dalet Nun Yud", "meaning": "Enough is Enough", "theme": "Enough", "duration": 12},
    {"id": 51, "name": "החש", "transliteration": "Hey Chet Shin", "meaning": "No Guilt", "theme": "No Guilt", "duration": 15},
    {"id": 52, "name": "עמם", "transliteration": "Ayin Mem Mem", "meaning": "Passion", "theme": "Passion", "duration": 10},
    {"id": 53, "name": "ננא", "transliteration": "Nun Nun Aleph", "meaning": "No Agenda", "theme": "No Agenda", "duration": 12},
    {"id": 54, "name": "נית", "transliteration": "Nun Yud Tav", "meaning": "Death of Death", "theme": "Death of Death", "duration": 15},
    {"id": 55, "name": "מבה", "transliteration": "Mem Bet Hey", "meaning": "Thought into Action", "theme": "Action", "duration": 10},
    {"id": 56, "name": "פוי", "transliteration": "Pe Vav Yud", "meaning": "Dispelling Anger", "theme": "Dispel Anger", "duration": 12},
    {"id": 57, "name": "נמם", "transliteration": "Nun Mem Mem", "meaning": "Listening to Your Soul", "theme": "Soul Listening", "duration": 15},
    {"id": 58, "name": "ייל", "transliteration": "Yud Yud Lamed", "meaning": "Letting Go", "theme": "Letting Go", "duration": 10},
    {"id": 59, "name": "הרח", "transliteration": "Hey Resh Chet", "meaning": "Umbilical Cord", "theme": "Umbilical Cord", "duration": 12},
    {"id": 60, "name": "מצר", "transliteration": "Mem Tzadi Resh", "meaning": "Freedom", "theme": "Freedom", "duration": 15},
    {"id": 61, "name": "ומב", "transliteration": "Vav Mem Bet", "meaning": "Water", "theme": "Water", "duration": 10},
    {"id": 62, "name": "יהה", "transliteration": "Yud Hey Hey", "meaning": "Parent-Teacher", "theme": "Parent-Teacher", "duration": 12},
    {"id": 63, "name": "ענו", "transliteration": "Ayin Nun Vav", "meaning": "Appreciation", "theme": "Appreciation", "duration": 15},
    {"id": 64, "name": "מחי", "transliteration": "Mem Chet Yud", "meaning": "Casting Yourself in a Favorable Light", "theme": "Favorable Light", "duration": 10},
    {"id": 65, "name": "דמב", "transliteration": "Dalet Mem Bet", "meaning": "Fear of God", "theme": "Fear of God", "duration": 12},
    {"id": 66, "name": "מנק", "transliteration": "Mem Nun Kof", "meaning": "Accountability", "theme": "Accountability", "duration": 15},
    {"id": 67, "name": "איע", "transliteration": "Aleph Yud Ayin", "meaning": "Great Expectations", "theme": "Great Expectations", "duration": 10},
    {"id": 68, "name": "חבו", "transliteration": "Chet Bet Vav", "meaning": "Contacting Departed Souls", "theme": "Contacting Souls", "duration": 12},
    {"id": 69, "name": "ראה", "transliteration": "Resh Aleph Hey", "meaning": "Lost and Found", "theme": "Lost and Found", "duration": 15},
    {"id": 70, "name": "יבם", "transliteration": "Yud Bet Mem", "meaning": "Recognizing Design Beneath Disorder", "theme": "Recognizing Design", "duration": 10},
    {"id": 71, "name": "היי", "transliteration": "Hey Yud Yud", "meaning": "Prophecy and Parallel Universes", "theme": "Prophecy", "duration": 12},
    {"id": 72, "name": "מום", "transliteration": "Mem Vav Mem", "meaning": "Spiritual Cleansing", "theme": "Cleansing", "duration": 15},
]

USERS = {}


@app.route("/")
def index():
    return render_template("index.html", names=NAMES[:3])


@app.route("/library")
def library():
    if not session.get("subscribed"):
        flash("Unlock demo access to view the full library", "warning")
        return redirect(url_for("index"))
    return render_template("library.html", names=NAMES)


@app.route("/session/<int:name_id>")
def session_view(name_id):
    if not session.get("subscribed"):
        flash("Unlock demo access to view sessions", "warning")
        return redirect(url_for("index"))
    name = next((n for n in NAMES if n["id"] == name_id), None)
    if not name:
        return redirect(url_for("library"))

    audio_path = os.path.join(app.static_folder, "audio", f"{name_id}.mp3")
    audio_available = os.path.exists(audio_path)
    return render_template("session.html", name=name, audio_available=audio_available)


@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email", "").strip().lower()
    if not email or "@" not in email:
        flash("Enter a valid email to unlock the demo library", "error")
        return redirect(url_for("index"))

    USERS[email] = {"subscribed": True}
    session.permanent = True
    session["subscribed"] = True
    session["email"] = email
    flash("Demo access unlocked. No payment was processed.", "success")
    return redirect(url_for("library"))


@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    if email in USERS and USERS[email].get("subscribed"):
        session["subscribed"] = True
        session["email"] = email
    else:
        flash("Email not found or not subscribed", "error")
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=env_flag_enabled("FLASK_DEBUG"), port=5000)
