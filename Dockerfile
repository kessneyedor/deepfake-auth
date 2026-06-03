FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libxcb1 \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install git+https://github.com/openai/CLIP.git

COPY . .

RUN mkdir -p data/images data/results

EXPOSE 7860

CMD ["python", "app.py"]