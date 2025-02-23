# Dockerfile
FROM python:3.11.7-slim AS python3_11_base

# Update pip
RUN pip config set global.extra-index-url "https://mirrors.cernet.edu.cn/pypi/web/simple" \
    && pip install --upgrade pip
    
# Set work directory
WORKDIR /app

FROM python3_11_base

# Copy requirements files and install packages
COPY requirements.txt /app/	

RUN chmod -R 755 /app \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*
	
# Copy all files from the current directory to the workdir in the container
COPY . /app

RUN chmod -R 755 /app