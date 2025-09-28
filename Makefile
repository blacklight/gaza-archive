.PHONY: all frontend

frontend:
	docker-compose --profile build up frontend-build

all: frontend
