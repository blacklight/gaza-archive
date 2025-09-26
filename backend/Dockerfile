FROM python:3.13-alpine

WORKDIR /

COPY requirements.txt .
COPY backend/gaza_archive /app

RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt && \
    find /venv -type f -name '*.pyc' -exec rm -f {} + && \
    find . -type f -name '*.pyc' -exec rm -f {} + && \
    rm -f requirements.txt

ENV PATH="/venv/bin:$PATH"

CMD ["/venv/bin/python", "-m", "app"]
