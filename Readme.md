# 🩺 ANE Arabic Medical Note Taker

This MVP is a **Streamlit-based Arabic-language note-taking app** designed for emergency room (ANE) doctors to record, transcribe, and summarize conversations with patients.

## 🚀 Features
- 🎙️ Live audio recording (Arabic)
- 🧑‍⚕️ Voice-based doctor identification
- 📋 Auto transcription using OpenAI Whisper
- 🧠 Medical summary generation using GPT-4
- 📈 Post-session analysis (symptom keywords, possible diagnoses)
- 🗂️ Patient/session management via PostgreSQL
- 📄 PDF export of structured clinical notes

---

## 📁 Project Structure
```bash
arabic_medical_note_mvp/
├── app.py                   # Streamlit app entry point
├── requirements.txt         # Dependencies
├── .env                     # API keys and DB config
│
├── audio/
│   └── recorder.py          # Audio recorder widget
├── db/
│   └── models.py            # PostgreSQL models & queries
├── nlp/
│   ├── transcribe.py        # Arabic transcription
│   ├── summarize.py         # GPT-based summarization
│   └── analyze.py           # Symptom & diagnosis extraction
├── ui/
│   ├── auth.py              # Voice-based doctor login
│   └── session_ui.py        # Main session interface
├── utils/
│   └── helpers.py           # PDF export and utilities
```

---

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/your-org/arabic-medical-note-mvp.git
cd arabic-medical-note-mvp
```

### 2. Create a `.env` file
```ini
OPENAI_API_KEY=your_openai_key
POSTGRES_DB=your_db
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
streamlit run app.py
```

---

## 🧪 Notes
- Requires a working **microphone** for live voice capture.
- You need a valid **OpenAI API Key** with access to `whisper-1` and `gpt-4`.
- Make sure **PostgreSQL** is running and accessible.

---

## 📦 Optional: Docker (coming soon)
We'll add a Dockerfile for GCP-ready deployment.

---

## 🧑‍💻 Authors & Credits
Built by ML & AI team for medical documentation automation. Inspired by real ER doctor workflows.

---

## 📬 Feedback / Issues
Please open an issue or contact the ML engineering team.

---

> Built for Arabic medical excellence 🇸🇦
