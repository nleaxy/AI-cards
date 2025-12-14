# 🧠 AI Study Cards

A powerful web application that leverages AI to automatically generate study flashcards from PDF documents. Upload your study materials, and the AI will extract key concepts to help you learn faster and more efficiently.

## ✨ Features

- **📄 PDF to Flashcards**: Upload any PDF document (lectures, textbooks), and the AI will generate a structured deck of questions and answers.
- **💾 Secured Storage**: Uses **MinIO** (S3-compatible) for robust and scalable file storage.
- **📊 Smart Statistics**: Track your learning progress, daily streaks, and the number of unique cards mastered.
- **🎨 Customization**: Personalize your decks with custom emoji icons.
- **🔄 Anki Support**: Export any deck to CSV format for seamless integration with Anki.
- **📱 Modern UI**: A responsive, clean interface built with React and TypeScript.

## 🛠️ Tech Stack

- **Frontend**: React, TypeScript, Lucide React, CSS Modules.
- **Backend**: Python, Flask, SQLAlchemy, Flask-JWT-Extended.
- **Storage**: MinIO (Object Storage), SQLite (Database).
- **AI**: LLM Integration for text processing and card generation.

## 🚀 Getting Started

### Prerequisites

- **Python** 3.8+
- **Node.js** 14+
- **MinIO Server** (Binary included or Docker)

### 1. Storage Setup (MinIO)

The project relies on MinIO for storing PDF files. We have included a helper script for Windows.

1. Run the start script in the root directory:
   ```cmd
   .\start_minio.bat
   ```
   *This will start the MinIO server on port 9000 and the console on 9001.*

### 2. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the server:
   ```bash
   python app.py
   ```
   *The backend will run at `http://localhost:5000`.*

### 3. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm start
   ```
   *The application will open automatically at `http://localhost:3000`.*

## 📝 Configuration

You can configure the application by creating a `.env` file in the `backend` directory or modifying `backend/config.py`. Key variables include:

- `SECRET_KEY`: App security key.
- `MINIO_ENDPOINT`: URL for MinIO (default: `localhost:9000`).
- `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY`: Credentials for MinIO.

## 🤝 Contributing

Feel free to fork this project and submit pull requests. Any improvements to the card generation logic or UI are welcome!

## 📄 License

This project is open-source and ready for personal or educational use.
