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
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libu2f-udev \
    libvulkan1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
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

COPY main.py .
COPY mode_submit.py .
COPY mode_sql_inject.py .
COPY utils.py .
COPY form_config.json .
COPY random_data.json .

ENV FORM_CONFIG="default"
ENV VERBOSITY="balanced"
ENV MIN_INTERVAL=""
ENV MAX_INTERVAL=""
ENV TARGET_URL=""
ENV DOCKER_CONTAINER="true"
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"] 