.PHONY: all frontend frontend-clean clean

frontend:
	docker-compose --profile build up frontend-build

frontend-clean:
	rm -rf frontend/dist
	docker-compose --profile build down --volumes --remove-orphans

all: frontend

clean: frontend-clean
