# Abundance AI Suite

A powerful AI-driven platform for content generation and retrieval, featuring:

- Advanced chat functionality with multiple sessions
- Document management with Retrieval-Augmented Generation (RAG)
- Token-based usage system with admin controls
- Modern Streamlit UI with FastAPI backend

## Project Structure

```
abundance_ai_suite/
├── backend/               # FastAPI backend
│   ├── app/               # Application code
│   │   ├── main.py        # FastAPI app entrypoint
│   │   ├── core/          # Core configuration
│   │   ├── crud/          # Database operations
│   │   ├── db/            # Database models and connection
│   │   ├── apis/          # API endpoints
│   │   ├── services/      # Business logic
│   │   └── schemas/       # Pydantic models
│   ├── .env               # Environment variables (create from .env.example)
│   └── requirements.txt   # Python dependencies
├── frontend/              # Streamlit frontend
│   ├── streamlit_app.py   # Main Streamlit app
│   ├── pages/             # Streamlit pages
│   ├── components/        # Reusable UI components
│   ├── services/          # API client services
│   ├── utils/             # Utility functions
│   └── requirements.txt   # Python dependencies
└── rag_data/              # Local storage for RAG (dev only)
    ├── uploaded_files/    # Raw uploaded documents
    └── vector_indexes/    # FAISS vector indexes
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- MongoDB (local or Atlas)
- Groq API key (for LLM)

### Backend Setup

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Create a virtual environment and activate it:

   ```bash
   python -m venv env
   # Windows
   env\Scripts\activate
   # macOS/Linux
   source env/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file (copy from `.env.example`) and configure with your credentials:

   ```
   MONGODB_URI=mongodb://localhost:27017
   MONGODB_DB_NAME=abundance_ai_suite
   SECRET_KEY=your_secret_key_here
   GROQ_API_KEY=your_groq_api_key_here
   ```

5. Start the backend server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Create a virtual environment and activate it:

   ```bash
   python -m venv env
   # Windows
   env\Scripts\activate
   # macOS/Linux
   source env/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the Streamlit app:

   ```bash
   streamlit run streamlit_app.py
   ```

5. Access the app in your browser at http://localhost:8501

### MongoDB Setup

1. Install MongoDB Community Edition or use MongoDB Atlas (cloud)
2. For local installation:

   ```bash
   # Start MongoDB service
   # Windows (as a service):
   net start MongoDB
   # macOS/Linux:
   sudo systemctl start mongod
   ```

3. The backend will automatically create necessary collections and indexes on first run

## Usage

1. Create an account or log in
2. Upload documents for RAG capabilities
3. Start chat sessions and interact with the AI
4. Admin users can manage users and token allocations

## Features

### Authentication & Authorization

- JWT-based authentication
- Role-based access control (admin/user)
- Secure password hashing

### Chat System

- Multiple chat sessions per user
- RAG-enabled responses
- Customizable system prompts
- Token usage tracking

### Document Management

- Support for PDF, TXT, CSV, DOCX files
- Automatic document processing and embedding
- Vector search for relevant context retrieval

### Admin Panel

- User management (create/edit/delete)
- Token allocation control
- Usage statistics and monitoring

## Development

- Backend API docs available at http://localhost:8000/docs
- For production deployment, consider using Docker and a reverse proxy

## License

MIT
