#!/bin/bash

# ========================
# Darkdump Tor-enabled Runner Script
# ========================

# Get keyword from environment variable or fallback to default
# If $TARGET is set externally (e.g., via `docker run -e TARGET=...`), use it
# Otherwise, use "helloweb.com" as the default search keyword
TARGET=${TARGET:-"helloweb.com"}

# Start the Tor service in the background using the custom torrc config
# Output from Tor goes to a temporary log file (/tmp/tor.log)
echo "[*] Starting Tor..."
tor -f /etc/tor/torrc > /tmp/tor.log &
TOR_PID=$!  # Capture the background process PID for Tor (can be used later if needed)

# Wait for Tor to finish bootstrapping (reach 100%)
# The loop checks the Tor log repeatedly until it sees the "Bootstrapped 100%" line
echo "[*] Waiting for Tor to fully bootstrap..."
until grep -q "Bootstrapped 100% (done): Done" /tmp/tor.log; do
    sleep 1  # Sleep 1 second before checking again (avoid CPU overuse)
done
echo "[+] Tor is fully bootstrapped."

# Create a directory to save the results
mkdir -p /opt/darkdump/results

# Change into the working directory where the darkdump.py script is located
cd /opt/darkdump  # Make sure your Dockerfile sets this as the workdir or copies here

# Run the Python script with the keyword from $TARGET
# -q specifies the search keyword
# -a 20 means return up to 20 results
# --scrape enables scraping content from the found onion sites
# --proxy tells it to use Tor (SOCKS5) as the proxy
# The `tee` command shows the output in the terminal and saves it to darkdump_output.txt
echo "[*] Running darkdump.py with target: $TARGET"
SAFE_TARGET=$(echo "$TARGET" | sed 's/[^a-zA-Z0-9_\-]/_/g' | tr '[:upper:]' '[:lower:]')
python3 darkdump.py -q "$TARGET" -a 20 --scrape --proxy | tee "./results/darkdump_output_${SAFE_TARGET}.txt"

# Keep the container open for manual inspection
# This replaces the current process with an interactive shell
# exec /bin/bash
