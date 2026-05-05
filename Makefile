.PHONY: install migrate dev-bot dev-front build-front dev-tunnel-cf dev-tunnel-ngrok init-data test

install:
	pip install -r requirements.txt
	cd frontend && npm install

migrate:
	alembic upgrade head

dev-bot:
	python -m bot

dev-front:
	cd frontend && npm run dev

build-front:
	cd frontend && npm run build

PORT ?= 5173

dev-tunnel-cf:
	cloudflared tunnel --url http://localhost:$(PORT)

dev-tunnel-ngrok:
	ngrok http $(PORT)

USER_ID ?=

init-data:
	python scripts/make_init_data.py --user-id $(USER_ID)

test:
	pytest -q
