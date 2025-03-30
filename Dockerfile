FROM python:3.9-slim

# Install Chrome dependencies and Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    curl \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Chrome WebDriver
RUN wget -q "https://storage.googleapis.com/chrome-for-testing-public/134.0.6998.165/linux64/chromedriver-linux64.zip" \
    && unzip chromedriver-linux64.zip -d /usr/local/bin \
    && mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -r /usr/local/bin/chromedriver-linux64 \
    && rm chromedriver-linux64.zip

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY form_submitter.py .
COPY sql_injection_tester.py .
COPY form_config.json .
COPY random_data.json .

ENV FORM_CONFIG="default"
ENV VERBOSITY="balanced"
ENV MIN_INTERVAL=""
ENV MAX_INTERVAL=""
ENV TARGET_URL=""

CMD ["python", "form_submitter.py"] 