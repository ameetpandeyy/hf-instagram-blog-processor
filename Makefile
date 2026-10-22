.PHONY: install run test lint format docker-build docker-run clean

install:
pip install -r requirements.txt

run:
uvicorn app.main:app --reload --port 7860

test:
pytest tests/ -v --cov=services --cov=app

lint:
black --check app services tests

format:
black app services tests

docker-build:
docker build -t instagram-blog-processor .

docker-run:
docker run -p 7860:7860 --env-file .env instagram-blog-processor

clean:
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type d -name ".pytest_cache" -exec rm -rf {} +
