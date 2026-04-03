FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# WICHTIG: registriert "sg"
RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["sg", "web", "--host", "0.0.0.0"]