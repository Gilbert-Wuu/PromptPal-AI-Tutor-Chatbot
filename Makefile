.PHONY: dev api stop docker logs help

DOCKER_DIR = Database-setup

help:
	@echo "Usage:"
	@echo "  make api    — Docker + Backend only (use /docs for testing)"
	@echo "  make dev    — Docker + Backend + Frontend (full stack)"
	@echo "  make stop   — Stop all services"
	@echo "  make docker — Start Docker containers only"
	@echo "  make logs   — Tail backend logs"

# Most common: Docker + Backend only
api: docker
	@echo "→ Backend starting at http://127.0.0.1:8000"
	@echo "→ API docs at  http://127.0.0.1:8000/docs"
	uvicorn backend.app.main:app --reload --port 8000

# Full stack: Docker + Backend + Frontend
dev: docker
	@echo "→ Starting Backend + Frontend in parallel..."
	@trap 'kill 0' SIGINT; \
	uvicorn backend.app.main:app --reload --port 8000 & \
	(cd frontend && npm run dev) & \
	wait

# Docker containers only
docker:
	@echo "→ Starting Docker containers (Postgres + Weaviate)..."
	cd $(DOCKER_DIR) && docker compose up -d
	@echo "→ Waiting for containers to be ready..."
	@sleep 3

# Stop everything
stop:
	cd $(DOCKER_DIR) && docker compose stop
	@pkill -f "uvicorn backend.app.main" 2>/dev/null || true
	@pkill -f "next dev" 2>/dev/null || true
	@echo "→ All services stopped."

# Tail uvicorn logs (useful when running dev in background)
logs:
	@echo "→ Use Ctrl+C to stop tailing"
	tail -f /tmp/promptpal-backend.log 2>/dev/null || echo "No log file found. Run 'make api' first."
