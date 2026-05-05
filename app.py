from flask import Flask, render_template, request, redirect, url_for, session, flash
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY environment variable is required.")


def env_flag_enabled(name):
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}

NAMES = [
    {
        "id": 1,
        "name": "אֵם",
        "transliteration": "Em",
        "meaning": "Mother",
        "theme": "Nurturing",
        "duration": 10,
    },
    {
        "id": 2,
        "name": "יוֹבַל",
        "transliteration": "Yoval",
        "meaning": "Sound",
        "theme": "Joy",
        "duration": 12,
    },
    {
        "id": 3,
        "name": "נִצָּחִי",
        "transliteration": "Nitzachi",
        "meaning": "Victory",
        "theme": "Strength",
        "duration": 15,
    },
    {
        "id": 4,
        "name": "הֶגֶה",
        "transliteration": "Hegai",
        "meaning": "Thought",
        "theme": "Clarity",
        "duration": 10,
    },
    {
        "id": 5,
        "name": "קָּדוֹשׁ",
        "transliteration": "Kadosh",
        "meaning": "Holy",
        "theme": "Sacred",
        "duration": 12,
    },
    {
        "id": 6,
        "name": "יֵשׁ",
        "transliteration": "Yesh",
        "meaning": "Existence",
        "theme": "Being",
        "duration": 15,
    },
    {
        "id": 7,
        "name": "שָׁלוֹם",
        "transliteration": "Shalom",
        "meaning": "Peace",
        "theme": "Harmony",
        "duration": 10,
    },
    {
        "id": 8,
        "name": "אֱמוּנָה",
        "transliteration": "Emunah",
        "meaning": "Faith",
        "theme": "Trust",
        "duration": 12,
    },
    {
        "id": 9,
        "name": "חֶסֶד",
        "transliteration": "Chesed",
        "meaning": "Lovingkindness",
        "theme": "Grace",
        "duration": 15,
    },
    {
        "id": 10,
        "name": "רַחוּם",
        "transliteration": "Rachum",
        "meaning": "Merciful",
        "theme": "Compassion",
        "duration": 10,
    },
    {
        "id": 11,
        "name": "אַב",
        "transliteration": "Av",
        "meaning": "Father",
        "theme": "Protection",
        "duration": 12,
    },
    {
        "id": 12,
        "name": "תִּקּוּף",
        "transliteration": "Tikuf",
        "meaning": "Strength",
        "theme": "Power",
        "duration": 15,
    },
    {
        "id": 13,
        "name": "נָקָם",
        "transliteration": "Nakam",
        "meaning": "Vengeance",
        "theme": "Justice",
        "duration": 10,
    },
    {
        "id": 14,
        "name": "גָּדוֹל",
        "transliteration": "Gadol",
        "meaning": "Great",
        "theme": "Magnificence",
        "duration": 12,
    },
    {
        "id": 15,
        "name": "נוֹרָא",
        "transliteration": "Nora",
        "meaning": "Awesome",
        "theme": "Awe",
        "duration": 15,
    },
    {
        "id": 16,
        "name": "עֶלְיוֹן",
        "transliteration": "Elyon",
        "meaning": "Most High",
        "theme": "Divinity",
        "duration": 10,
    },
    {
        "id": 17,
        "name": "שַׁדַּי",
        "transliteration": "Shaddai",
        "meaning": "Almighty",
        "theme": "Omnipotence",
        "duration": 12,
    },
    {
        "id": 18,
        "name": "צַדִּיק",
        "transliteration": "Tzadik",
        "meaning": "Righteous",
        "theme": "Righteousness",
        "duration": 15,
    },
    {
        "id": 19,
        "name": "סַלָּה",
        "transliteration": "Sala",
        "meaning": "Forgiveness",
        "theme": "Release",
        "duration": 10,
    },
    {
        "id": 20,
        "name": "מָעוּז",
        "transliteration": "Maoz",
        "meaning": "Fortress",
        "theme": "Refuge",
        "duration": 12,
    },
    {
        "id": 21,
        "name": "דָּרֹור",
        "transliteration": "Daro",
        "meaning": "Freedom",
        "theme": "Liberation",
        "duration": 15,
    },
    {
        "id": 22,
        "name": "שַׁעַר",
        "transliteration": "Shaar",
        "meaning": "Gate",
        "theme": "Portal",
        "duration": 10,
    },
    {
        "id": 23,
        "name": "פְּנִיאֵל",
        "transliteration": "Peniel",
        "meaning": "Face of God",
        "theme": "Presence",
        "duration": 12,
    },
    {
        "id": 24,
        "name": "זִיו",
        "transliteration": "Ziv",
        "meaning": "Splendor",
        "theme": "Radiance",
        "duration": 15,
    },
    {
        "id": 25,
        "name": "אוֹר",
        "transliteration": "Or",
        "meaning": "Light",
        "theme": "Illumination",
        "duration": 10,
    },
    {
        "id": 26,
        "name": "חַיָּה",
        "transliteration": "Chayah",
        "meaning": "Living",
        "theme": "Life Force",
        "duration": 12,
    },
    {
        "id": 27,
        "name": "שְׁמוּאֵל",
        "transliteration": "Shmuel",
        "meaning": "Heard by God",
        "theme": "Answer",
        "duration": 15,
    },
    {
        "id": 28,
        "name": "מֵיטָב",
        "transliteration": "Meitiv",
        "meaning": "Best",
        "theme": "Excellence",
        "duration": 10,
    },
    {
        "id": 29,
        "name": "נוֹחַ",
        "transliteration": "Noach",
        "meaning": "Rest",
        "theme": "Peace",
        "duration": 12,
    },
    {
        "id": 30,
        "name": "שֵׁכָר",
        "transliteration": "Shechar",
        "meaning": "Reward",
        "theme": "Merit",
        "duration": 15,
    },
    {
        "id": 31,
        "name": "בִּרְכָּה",
        "transliteration": "Berachah",
        "meaning": "Blessing",
        "theme": "Abundance",
        "duration": 10,
    },
    {
        "id": 32,
        "name": "עֹשֶׁר",
        "transliteration": "Oshar",
        "meaning": "Wealth",
        "theme": "Prosperity",
        "duration": 12,
    },
    {
        "id": 33,
        "name": "כָּבוֹד",
        "transliteration": "Kavod",
        "meaning": "Glory",
        "theme": "Honor",
        "duration": 15,
    },
    {
        "id": 34,
        "name": "הָדָר",
        "transliteration": "Hadar",
        "meaning": "Majesty",
        "theme": "Grandeur",
        "duration": 10,
    },
    {
        "id": 35,
        "name": "תִּפְאֶרֶת",
        "transliteration": "Tiferet",
        "meaning": "Beauty",
        "theme": "Harmony",
        "duration": 12,
    },
    {
        "id": 36,
        "name": "נְעָמִים",
        "transliteration": "Neamim",
        "meaning": "Pleasantness",
        "theme": "Delight",
        "duration": 15,
    },
    {
        "id": 37,
        "name": "שָׂשׂוֹן",
        "transliteration": "Sason",
        "meaning": "Joy",
        "theme": "Gladness",
        "duration": 10,
    },
    {
        "id": 38,
        "name": "רִנָּה",
        "transliteration": "Rinah",
        "meaning": "Singing",
        "theme": "Praise",
        "duration": 12,
    },
    {
        "id": 39,
        "name": "תְּשׁוּבָה",
        "transliteration": "Teshuvah",
        "meaning": "Return",
        "theme": "Repentance",
        "duration": 15,
    },
    {
        "id": 40,
        "name": "צְדָקָה",
        "transliteration": "Tzedakah",
        "meaning": "Righteousness",
        "theme": "Justice",
        "duration": 10,
    },
    {
        "id": 41,
        "name": "חַיִּים",
        "transliteration": "Chaim",
        "meaning": "Life",
        "theme": "Vitality",
        "duration": 12,
    },
    {
        "id": 42,
        "name": "בְּרִיאָה",
        "transliteration": "Briah",
        "meaning": "Creation",
        "theme": "Origin",
        "duration": 15,
    },
    {
        "id": 43,
        "name": "חָכְמָה",
        "transliteration": "Chochmah",
        "meaning": "Wisdom",
        "theme": "Insight",
        "duration": 10,
    },
    {
        "id": 44,
        "name": "בִּינָה",
        "transliteration": "Binah",
        "meaning": "Understanding",
        "theme": "Discernment",
        "duration": 12,
    },
    {
        "id": 45,
        "name": "דַּעַת",
        "transliteration": "Daat",
        "meaning": "Knowledge",
        "theme": "Awareness",
        "duration": 15,
    },
    {
        "id": 46,
        "name": "עֵצָה",
        "transliteration": "Eitzah",
        "meaning": "Counsel",
        "theme": "Guidance",
        "duration": 10,
    },
    {
        "id": 47,
        "name": "גְּבוּרָה",
        "transliteration": "Gevurah",
        "meaning": "Might",
        "theme": "Strength",
        "duration": 12,
    },
    {
        "id": 48,
        "name": "תִּקַּת קָּלָה",
        "transliteration": "Tiharat Kola",
        "meaning": "Voice Purification",
        "theme": "Clarity",
        "duration": 15,
    },
    {
        "id": 49,
        "name": "מַלְאָךְ",
        "transliteration": "Malach",
        "meaning": "Angel",
        "theme": "Messenger",
        "duration": 10,
    },
    {
        "id": 50,
        "name": "רוּחַ",
        "transliteration": "Ruach",
        "meaning": "Spirit",
        "theme": "Breath",
        "duration": 12,
    },
    {
        "id": 51,
        "name": "נְשָׁמָה",
        "transliteration": "Neshamah",
        "meaning": "Soul",
        "theme": "Essence",
        "duration": 15,
    },
    {
        "id": 52,
        "name": "יְדִידוּת",
        "transliteration": "Yedidut",
        "meaning": "Friendship",
        "theme": "Love",
        "duration": 10,
    },
    {
        "id": 53,
        "name": "אַהֲבָה",
        "transliteration": "Ahavah",
        "meaning": "Love",
        "theme": "Devotion",
        "duration": 12,
    },
    {
        "id": 54,
        "name": "רַחֲבָה",
        "transliteration": "Rachavah",
        "meaning": "Spacious",
        "theme": "Expansion",
        "duration": 15,
    },
    {
        "id": 55,
        "name": "שַׁמַּיָּא",
        "transliteration": "Shammaya",
        "meaning": "There is Name",
        "theme": "Existence",
        "duration": 10,
    },
    {
        "id": 56,
        "name": "נִצָּחוּ",
        "transliteration": "Nitzachu",
        "meaning": "They Will Triumph",
        "theme": "Victory",
        "duration": 12,
    },
    {
        "id": 57,
        "name": "קַיָּמָא",
        "transliteration": "Kayama",
        "meaning": "Enduring",
        "theme": "Eternity",
        "duration": 15,
    },
    {
        "id": 58,
        "name": "יְקִירָא",
        "transliteration": "Yekira",
        "meaning": "Precious",
        "theme": "Value",
        "duration": 10,
    },
    {
        "id": 59,
        "name": "חֲבִיבָא",
        "transliteration": "Chaviva",
        "meaning": "Beloved",
        "theme": "Cherished",
        "duration": 12,
    },
    {
        "id": 60,
        "name": "שְׁפָרִיר",
        "transliteration": "Shfirim",
        "meaning": "Bright",
        "theme": "Clarity",
        "duration": 15,
    },
    {
        "id": 61,
        "name": "טָהוֹר",
        "transliteration": "Tahor",
        "meaning": "Pure",
        "theme": "Purity",
        "duration": 10,
    },
    {
        "id": 62,
        "name": "קָּדוֹשִׁים",
        "transliteration": "Kedoshim",
        "meaning": "Holy Ones",
        "theme": "Sanctity",
        "duration": 12,
    },
    {
        "id": 63,
        "name": "מַלְאָכִים",
        "transliteration": "Malachim",
        "meaning": "Angels",
        "theme": "Messengers",
        "duration": 15,
    },
    {
        "id": 64,
        "name": "שָׁמַיִם",
        "transliteration": "Shamayim",
        "meaning": "Heavens",
        "theme": "Divine Realm",
        "duration": 10,
    },
    {
        "id": 65,
        "name": "אָרֶץ",
        "transliteration": "Eretz",
        "meaning": "Earth",
        "theme": "Material World",
        "duration": 12,
    },
    {
        "id": 66,
        "name": "יָם",
        "transliteration": "Yam",
        "meaning": "Sea",
        "theme": "Depths",
        "duration": 15,
    },
    {
        "id": 67,
        "name": "נָהָר",
        "transliteration": "Nahar",
        "meaning": "River",
        "theme": "Flow",
        "duration": 10,
    },
    {
        "id": 68,
        "name": "אֲרָיוֹת",
        "transliteration": "Arayot",
        "meaning": "Lions",
        "theme": "Courage",
        "duration": 12,
    },
    {
        "id": 69,
        "name": "שַׁחַר",
        "transliteration": "Shachar",
        "meaning": "Dawn",
        "theme": "New Beginnings",
        "duration": 15,
    },
    {
        "id": 70,
        "name": "עֶרֶב",
        "transliteration": "Erev",
        "meaning": "Evening",
        "theme": "Completion",
        "duration": 10,
    },
    {
        "id": 71,
        "name": "לַיְלָה",
        "transliteration": "Laila",
        "meaning": "Night",
        "theme": "Rest",
        "duration": 12,
    },
    {
        "id": 72,
        "name": "כֹּל",
        "transliteration": "Kol",
        "meaning": "All",
        "theme": "Wholeness",
        "duration": 15,
    },
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
