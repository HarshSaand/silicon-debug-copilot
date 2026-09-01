.PHONY: install test benchmark api app docker-up docker-down

install:
	python -m pip install -e '.[test]'

test:
	python -m pytest

benchmark:
	python scripts/generate_incidents.py
	python scripts/build_index.py
	python scripts/evaluate.py --split test --output evals/baseline_results.json
	python scripts/evaluate.py --split test --core --output evals/core_results.json

api:
	uvicorn silicon_debug.api:app --app-dir src --reload

app:
	streamlit run app.py

docker-up:
	docker compose up --build

docker-down:
	docker compose down
