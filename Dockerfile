FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y git tor curl && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/darkdump

# Copy Tor configuration
COPY torrc /etc/tor/torrc

# Clone the original repo (we'll override the script below)
RUN git clone https://github.com/josh0xA/darkdump.git /opt/darkdump

# Overwrite darkdump.py with your custom JSON-support version
COPY darkdump.py ./darkdump.py

# Copy your run script
COPY run_darkdump.sh ./run_darkdump.sh
RUN chmod +x ./run_darkdump.sh

# Copy requirements if modified (optional safety net)
COPY requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install -r requirements.txt

# Install socks and NLTK corpora (just in case not in requirements.txt)
RUN pip install "requests[socks]"
RUN python3 -m textblob.download_corpora

# Expose Tor SOCKS port
EXPOSE 9050

# Default command
CMD ["./run_darkdump.sh"]
