FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

# Set the FLASK_APP environment variable
ENV FLASK_APP=app.py
# Set Flask to run on port 80
ENV PORT=80

# Run Flask
CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]
