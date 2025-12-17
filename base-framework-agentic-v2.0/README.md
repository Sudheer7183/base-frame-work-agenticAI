# Agentic AI Platform v1.3 (Complete)

## Features
- ✅ FastAPI backend with SQLAlchemy ORM
- ✅ Keycloak authentication & RBAC
- ✅ Multi-tenancy with PostgreSQL schemas
- ✅ LangGraph agent framework
- ✅ Human-in-the-Loop (HITL) system
- ✅ React admin dashboard
- ✅ Streamlit HITL interface
- ✅ Complete API with validation
- ✅ Production-ready deployment configs

## Quick Start

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your configuration

# 2. Start infrastructure
docker compose up -d

# 3. Install backend
cd backend
pip install -r requirements.txt
alembic upgrade head

# 4. Install frontend
cd ../frontend/react-admin
npm install

# 5. Start services
# Terminal 1: Backend
cd backend && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend/react-admin && npm run dev

# Terminal 3: HITL UI
cd frontend/streamlit-hitl && streamlit run app.py
```

## Access Points
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Admin UI: http://localhost:3000
- HITL UI: http://localhost:8501

## Documentation
See `docs/` directory for detailed guides.
