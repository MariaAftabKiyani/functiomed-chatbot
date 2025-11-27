# Functiomed Chatbot

Medical chatbot with RAG capabilities using Qdrant vector database.

## Setup

### Prerequisites
- Python 3.8+
- Qdrant (running on localhost:6333)

### Installation

1. Clone and navigate to project:
```bash
cd functiomed-chatbot
```

2. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
```
Edit `.env` with your Qdrant configuration.

4. Run backend:
```bash
cd backend
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend

Open `frontend/wordpress-widget/v1/chatbot.html` in your browser.
