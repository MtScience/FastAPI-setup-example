format:
	poetry run isort src tests main.py
	poetry run black src tests main.py

flake:
	poetry run flake8 src tests main.py

mypy:
	poetry run mypy src tests main.py

start: stop
	docker compose up --build

start_bg: stop
	docker compose up --build -d

stop:
	docker compose down --remove-orphans

test: stop
	docker compose -f docker-compose-test.yml run --rm --build tests
