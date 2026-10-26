from flask import Flask, Response, abort, render_template, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
import os

app = Flask(__name__)

# Vercel terminates TLS in front of us; without this, canonical links, OG image
# URLs and the sitemap would all be generated as http://.
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# The app is stateless: no accounts, no cookies, nothing to sign. That is why
# there is no SECRET_KEY here — an absent secret used to be a hard failure, but
# without sessions the "forgeable cookie" risk it guarded against cannot exist.
# If a cookie-backed feature is added later, require SECRET_KEY at that point
# and never fall back to a hardcoded default.


def env_flag_enabled(name):
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}

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


@app.route("/")
def index():
    return render_template("index.html", names=NAMES[:6])


@app.route("/library")
def library():
    return render_template("library.html", names=NAMES)


@app.route("/session/<int:name_id>")
def session_view(name_id):
    name = next((n for n in NAMES if n["id"] == name_id), None)
    if not name:
        abort(404)

    audio_path = os.path.join(app.static_folder, "audio", f"{name_id}.mp3")
    audio_available = os.path.exists(audio_path)
    return render_template(
        "session.html",
        name=name,
        audio_available=audio_available,
        previous=NAMES[(name_id - 2) % len(NAMES)],
        following=NAMES[name_id % len(NAMES)],
    )


@app.route("/sitemap.xml")
def sitemap():
    paths = [url_for("index"), url_for("library")]
    paths += [url_for("session_view", name_id=n["id"]) for n in NAMES]

    root = url_for("index", _external=True).rstrip("/")
    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    body += [f"  <url><loc>{root}{path}</loc></url>" for path in paths]
    body.append("</urlset>")
    return Response("\n".join(body) + "\n", mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    return Response(
        f"User-agent: *\nAllow: /\n\nSitemap: {url_for('sitemap', _external=True)}\n",
        mimetype="text/plain",
    )


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=env_flag_enabled("FLASK_DEBUG"), port=5000)
