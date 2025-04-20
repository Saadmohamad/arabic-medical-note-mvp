# ANE Arabic Medical Note Taker

A Streamlit-based MVP for Arabic-language clinical note-taking, designed to streamline doctor–patient interactions in emergency settings.

---

## 🚀 Features
- **Automatic Transcription**: Leverage OpenAI Whisper (`whisper-1`) for high-quality Arabic transcription.
- **AI-Powered Summarization**: Generate structured clinical notes using GPT-4.
- **Post-Session Analysis**: Extract symptom keywords and suggest possible diagnoses with GPT-4o-mini.
- **Session Management**: Store doctors, patients, and session data in PostgreSQL.
- **PDF Export**: Produce downloadable, RTL-formatted clinical summaries and transcripts.
- **History & Review**: Browse recent sessions via sidebar.

---

## 📦 Project Structure

```
arabic_medical_note_mvp/
├── **app.py**                # Streamlit entry point and sidebar navigation
├── **requirements.txt**      # Python dependencies
├── **.env**                  # Environment variables (API keys, DB config)
│
├── **ui/**
│   ├── **auth.py**           # Voice authentication helper (not yet integrated into session flow)
│   └── **session_ui.py**     # Interactive session UI flow
│
├── **nlp/**
│   ├── **transcribe.py**     # Arabic transcription + speaker tagging
│   ├── **summarise.py**      # GPT-4 summarization component
│   ├── **analyse.py**        # Symptom & diagnosis extraction with GPT-4o-mini
│   └── **utils.py**          # Arabic normalization utilities
│
├── **db/**
│   └── **models.py**         # PostgreSQL schema & CRUD operations
│
├── **utils/**
│   └── **helpers.py**        # PDF export, RTL wrapping, font utilities
│
└── **.pre-commit-config.yaml**  # Code formatting & linting hooks
```

---

## ⚙️ Setup & Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-org/arabic-medical-note-mvp.git
   cd arabic-medical-note-mvp
   ```

2. **Configure environment variables**

   Create a `.env` file in the project root:

   ```dotenv
   OPENAI_API_KEY=your_openai_key
   POSTGRES_DB=your_db_name
   POSTGRES_USER=your_db_user
   POSTGRES_PASSWORD=your_db_password
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**

   Ensure PostgreSQL is running, then start the app (the DB tables will be auto-created):

   ```bash
   streamlit run app.py
   ```

---

## 🧑‍💻 Usage

- **Start a New Session**: Click **Start New Session** in the sidebar.
- **Doctor & Patient**: Input the doctor's name (Arabic) via text or voice helper.
- **Record Conversation**: Capture the patient interaction with the audio widget.
- **Review & Edit**: View full transcript, edit AI-generated summary fields.
- **Export**: Download a formatted PDF of the clinical note.
- **History**: Review recent sessions from the sidebar.

---

## 🧪 Notes & Requirements

- **Microphone Access**: Required for live recording.
- **OpenAI Access**: Whisper (`whisper-1`), GPT-4, and GPT-4o-mini models.
- **PostgreSQL**: Running and accessible per `.env` settings.
- **RTL Support**: Uses DejaVu Unicode font; ensure font availability.

---

## 🧑‍🤝‍🧑 Contributors

- **ML & AI Team**: Core development and design.
- **Streamlit Community**: st-audiorec widget integration.

---

## 📬 Feedback & Issues

Please open an issue or contact the ML engineering team for questions or feature requests.

---

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for details.
