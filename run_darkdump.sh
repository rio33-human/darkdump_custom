#!/bin/bash

# Get keyword from env or default
TARGET=${TARGET:-"helloweb.com"}

# Start Tor in background
echo "[*] Starting Tor..."
tor -f /etc/tor/torrc > /tmp/tor.log &
TOR_PID=$!

# Wait for full bootstrap
echo "[*] Waiting for Tor to fully bootstrap..."
until grep -q "Bootstrapped 100% (done): Done" /tmp/tor.log; do
    sleep 1
done
echo "[+] Tor is fully bootstrapped."

# Run Darkdump
cd /opt/darkdump
echo "[*] Running darkdump.py with target: $TARGET"
python3 darkdump.py -q "$TARGET" -a 20 --scrape --proxy | tee darkdump_output.txt

# Drop to shell for inspection
exec /bin/bash
