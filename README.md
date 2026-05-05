# ✧ 72 Names Meditations

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Immersive spiritual practice meet modern technology.** 

72 Names Meditations is a focused, elegant Flask application designed to facilitate deep meditation through the sacred 72 Names of God. Unlike traditional reference apps, this platform provides an immersive audio-guided experience designed for daily mindfulness and spiritual elevation.

![App Screenshot](https://raw.githubusercontent.com/fayerman-source/72-names/main/static/banner.png) *(Note: Add your own banner or screenshot here)*

## ✨ Key Features

- **🛡️ Secure & Lightweight:** Built with Flask, emphasizing security-first session management and environment-based configuration.
- **🎧 Local Audio Synthesis:** Integrated `ffmpeg` utility to generate placeholder meditative tones for all 72 names locally.
- **✨ Immersive UI:** A premium, dark-themed interface crafted for distraction-free practice.
- **📖 Sacred Catalog:** Complete library of Hebrew names, transliterations, and spiritual themes.
- **🚀 Deploy-Ready:** Optimized for Vercel and production-ready environments with environment variable protection.

## 🛠️ Quick Start

### 1. Prerequisites
Ensure you have Python 3.10+ and `ffmpeg` (for audio generation) installed.

### 2. Installation
```bash
git clone https://github.com/fayerman-source/72-names.git
cd 72-names
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Local Environment
```bash
cp .env.example .env
# Edit .env and set a secure SECRET_KEY
```

### 4. Generate Audio Assets
To synthesize the meditative placeholder tones:
```bash
python generate_audio.py
```

### 5. Launch
```bash
flask --app app run --debug
```
Visit `http://127.0.0.1:5000` to begin your session.

## 🧪 Testing
We maintain high standards for our core logic:
```bash
pip install -r requirements-dev.txt
pytest
```

## 🗺️ Roadmap
- [ ] High-fidelity studio recordings for all 72 sessions.
- [ ] Persistent user progress tracking.
- [ ] Advanced filtering by spiritual theme (e.g., Healing, Abundance, Protection).
- [ ] Mobile-first PWA enhancements.

## 🤝 Contributing
Contributions are welcome! Whether it's improving the meditation scripts, refining the UI, or adding new features, please feel free to open a PR.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Created with intention for the global spiritual community.*
