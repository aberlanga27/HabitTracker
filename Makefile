VENV := $(CURDIR)/.venv/bin

.PHONY: demo demo-shutdown

# Backend on :8000 and frontend on :5173; Ctrl+C stops both.
demo:
	@[ -d src/frontend/node_modules ] || (cd src/frontend && npm install)
	@cd src/backend && $(VENV)/alembic upgrade head
	@trap 'kill $$(jobs -p) 2>/dev/null' INT TERM EXIT; \
	(cd src/backend && exec $(VENV)/uvicorn app.main:app --reload --port 8000) & \
	(cd src/frontend && exec npm run dev -- --strictPort) & \
	wait

# Stops a demo started from any terminal; only listeners on the demo ports are killed.
# An orphaned uvicorn reloader can ignore SIGTERM, hence the SIGKILL fallback.
demo-shutdown:
	@pids="$$(lsof -ti tcp:8000 -sTCP:LISTEN; lsof -ti tcp:5173 -sTCP:LISTEN; \
		pgrep -f '^[^ ]*[Pp]ython[^ ]* [^ ]*uvicorn app\.main:app')"; \
	if [ -n "$$pids" ]; then \
		kill $$pids 2>/dev/null; sleep 2; kill -9 $$pids 2>/dev/null; \
	fi; \
	echo "Demo stopped (ports 8000 and 5173 are free)."
