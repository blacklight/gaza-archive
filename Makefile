.PHONY: all frontend frontend-clean clean

frontend:
	cd frontend && npm ci && npm run build

frontend-clean:
	rm -rf frontend/dist

all: frontend

clean: frontend-clean
