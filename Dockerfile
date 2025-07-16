# Multi-stage build for better caching and smaller final image
FROM python:3.12-slim as base

# Install system dependencies (rarely changes - good for caching)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Stage 1: Python dependencies (cache this layer when requirements.txt doesn't change)
FROM base as python-deps
COPY ./backend/requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip setuptools wheel -i https://pypi.tuna.tsinghua.edu.cn/simple

# Install PyTorch with CUDA support (separate layer for better caching)
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install other Python dependencies
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir jieba -i https://pypi.tuna.tsinghua.edu.cn/simple

# Stage 2: NLTK data (cache this layer)
FROM python-deps as nltk-data
ENV NLTK_DATA /usr/local/share/nltk_data
RUN mkdir -p $NLTK_DATA && \
    python -m nltk.downloader -d $NLTK_DATA punkt stopwords vader_lexicon punkt_tab

# Stage 3: Whisper models (cache this layer - only changes when we want different models)
FROM nltk-data as whisper-models
RUN mkdir -p /root/.cache/whisper && \
    echo "📥 Pre-downloading Whisper models for instant access..." && \
    python -c "import whisper; import os; \
    print('📥 Downloading Large V3 model...'); \
    model = whisper.load_model('large-v3'); \
    print('📥 Downloading Turbo backup model...'); \
    model2 = whisper.load_model('turbo'); \
    print('✅ All models successfully cached'); \
    import glob; models = glob.glob('/root/.cache/whisper/*.pt'); \
    [print(f'  ✓ {os.path.basename(m)}') for m in models]" && \
    ls -la /root/.cache/whisper/

# Final stage: Application code (this layer changes most frequently)
FROM whisper-models as final

# Create non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy application code (this layer will rebuild when code changes)
COPY ./backend /app/backend

# Set environment
ENV PYTHONPATH "${PYTHONPATH}:/app"
EXPOSE 8008

# Command will be specified in docker-compose 