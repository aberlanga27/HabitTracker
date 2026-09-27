VENV := $(CURDIR)/.venv/bin

.PHONY: demo demo-shutdown

# Backend on :8000 and frontend on :5173; Ctrl+C stops both.
demo:
	@[ -d src/frontend/node_modules ] || (cd src/frontend && npm install)
	@cd src/backend && $(VENV)/alembic upgrade head
	@trap 'kill 0' INT TERM EXIT; \
	(cd src/backend && $(VENV)/uvicorn app.main:app --reload --port 8000) & \
	(cd src/frontend && npm run dev) & \
	wait

# Stops a demo started from any terminal; only listeners on the demo ports are killed.
demo-shutdown:
	@pkill -f "uvicorn app.main:app --reload --port 8000" 2>/dev/null || true
	@lsof -ti tcp:8000 -sTCP:LISTEN | xargs kill 2>/dev/null || true
	@lsof -ti tcp:5173 -sTCP:LISTEN | xargs kill 2>/dev/null || true
	@echo "Demo stopped (ports 8000 and 5173 are free)."
