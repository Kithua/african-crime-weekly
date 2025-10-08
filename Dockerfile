FROM python:3.11-slim
RUN apt-get update && apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libffi-dev curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download xx_ent_wiki_sm
COPY . .
CMD ["python", "-m", "src.main"]
