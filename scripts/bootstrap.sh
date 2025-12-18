#!/usr/bin/env bash
set -e

echo "🚀 Bootstrapping Agentic AI Platform..."

# Check prerequisites
command -v docker >/dev/null || { echo "Docker required"; exit 1; }
command -v python3 >/dev/null || { echo "Python required"; exit 1; }

# Start infrastructure
echo "📦 Starting infrastructure..."
docker compose -f infra/docker-compose.yml up -d

# Backend setup
echo "🐍 Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Frontend setup
echo "🖥️  Setting up frontend..."
cd ../frontend/react-admin
npm install
cd ../frontend/streamlit-hitl
pip install -r requirements.txt
echo "✅ Bootstrap complete!"
echo ""
echo "Start services:"
echo "  Backend: cd backend && uvicorn app.main:app --reload"
echo "  Frontend: cd frontend/react-admin && npm run dev"
echo "  HITL: cd frontend/streamlit-hitl && streamlit run app.py"
