FROM python:3.13-alpine

WORKDIR /app

COPY requirements.txt .
COPY gaza_archive .

RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt && \
    find /venv -type f -name '*.pyc' -exec rm -f {} + && \
    find ./gaza_archive -type f -name '*.pyc' -exec rm -f {} +

ENV PATH="/venv/bin:$PATH"

USER nobody

CMD ["/venv/bin/python", "-m", "gaza_archive"]
