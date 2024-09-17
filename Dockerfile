FROM python:3.9-slim

WORKDIR /app

COPY . .
RUN pip install --upgrade pip && \
    pip install -e .

EXPOSE 8000 8001

CMD ["start-server", "--port", "8000"]
