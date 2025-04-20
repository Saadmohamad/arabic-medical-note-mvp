# 📝 Arabic Medical Note Taker for Emergency Rooms (ANE)

A bilingual Streamlit app for recording, transcribing, summarizing, and analyzing Arabic doctor-patient conversations in emergency rooms. Tailored for Arabic-speaking clinicians, with RTL layout, secure login, and PDF export of clinical notes.

---

## 🚀 Features

- 🔐 **Secure Login** – Sign up, log in, and manage sessions with email & password
- 👨‍⚕️ **Doctor–Patient Selection** – Identify session participants and date
- 🎤 **Audio Recording** – Record patient interviews directly from the browser
- 🧠 **AI-Powered Processing**:
  - 🗣️ Whisper for **Arabic speech-to-text**
  - ✍️ GPT-4 for **structured clinical summaries**
- 🪴 **Medical NLP Analysis**:
  - Extracts **symptom keywords**
  - Suggests **possible diagnoses**
- 📄 **PDF Export**:
  - Generate Arabic summaries with transcript
  - RTL formatting with reshaped font
- 📂 **Session History**:
  - Browse past sessions
  - Edit and re-export summaries

---

## 🗄️ Workflow

1. 🔐 Login or Sign Up
2. 📟 Select doctor, patient, and date
3. 🎤 Record audio
4. 🧠 AI transcribes and summarizes
5. 📝 Review and edit the auto-filled summary
6. 📄 Export as Arabic PDF
7. 📂 Revisit past sessions anytime

---

## 🩰 Tech Stack

| Layer        | Technology                          |
|--------------|-------------------------------------|
| Frontend     | [Streamlit](https://streamlit.io)   |
| Backend      | PostgreSQL, Custom ORM (Python)     |
| AI Services  | OpenAI Whisper + GPT-4              |
| Audio Input  | `streamlit-audiorec`                |
| PDF Output   | `fpdf2`, `arabic_reshaper`, `bidi`  |

---

## 🛠️ Setup Instructions

### 1. Clone the repo

```bash
git clone https://github.com/your-org/arabic-medical-note-taker.git
cd arabic-medical-note-taker
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env` file

```env
OPENAI_API_KEY=your_openai_key
POSTGRES_DB=your_db
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=your_host
POSTGRES_PORT=5432
```

### 4. Initialize the database

```python
from db.models import setup_database
setup_database()
```

Or just run the app once – it sets up automatically.

### 5. Run the app

```bash
streamlit run app.py
```

---

## 📁 Folder Structure

```
.
├── app.py                   # Main app entry
├── db/                      # User, doctor, patient, session logic
├── nlp/                     # Transcription, summary, diagnosis
├── ui/                      # UI flows (login, session wizard)
├── utils/                   # PDF generation, text helpers
├── fonts/                   # DejaVuSans.ttf for Arabic support
├── .env                     # Your API/DB config
├── requirements.txt
└── README.md
```

---

## 🧪 Dev Notes

### Pre-commit Setup

```bash
pre-commit install
```

Includes:

- `black` – formatting
- `ruff` – linting
- `mypy` – type checking

### Font Note

Ensure `fonts/DejaVuSans.ttf` exists. It’s required for Arabic PDF export.

---

## ✅ TODOs / Roadmap

- [ ] Password reset via email
- [ ] Mobile responsiveness
- [ ] Audio upload support (for pre-recorded .wav/.mp3)
- [ ] Admin dashboard
- [ ] Session deletion and search

---

## 🙏 Acknowledgments

- [OpenAI](https://openai.com) for Whisper and GPT-4
- [Streamlit](https://streamlit.io) for the amazing app framework
- `arabic_reshaper` + `python-bidi` for RTL PDF rendering

---

## 📜 License

MIT License
