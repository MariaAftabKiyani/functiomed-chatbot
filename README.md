# Functiomed Chatbot

Medical chatbot with RAG capabilities using Qdrant vector database.

## Setup

### Prerequisites
- Python 3.8+
- Docker

### Installation

1. Start Qdrant with Docker:
```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 -p 6334:6334 -v "$(pwd)/qdrant_storage:/qdrant/storage:z" qdrant/qdrant
```

2. Clone and navigate to project:
```bash
cd functiomed-chatbot
```

3. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
```
Edit `.env` with your Qdrant configuration.

5. Run backend:
```bash
cd backend
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend

Open `frontend/wordpress-widget/v1/chatbot.html` in your browser.
