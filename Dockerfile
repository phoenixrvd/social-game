FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && git config --global user.name "Social Game" \
    && git config --global user.email "social-game@local" \
    && git config --global init.defaultBranch main \
    && git config --global safe.directory /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# WICHTIG: registriert "sg"
RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["sg", "web", "--host", "0.0.0.0"]
