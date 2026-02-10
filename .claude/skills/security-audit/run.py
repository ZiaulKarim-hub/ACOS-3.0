#!/usr/bin/env python3

import time
import os
from zapv2 import ZAPv2

# Get the target URL from an environment variable
target_url = os.getenv('TARGET_URL')
if not target_url:
    print("Error: TARGET_URL environment variable not set.")
    exit(1)

# ZAP API key and proxy settings
# Make sure ZAP is running and the API key is set correctly.
apikey = os.getenv('ZAP_API_KEY')
zap = ZAPv2(apikey=apikey, proxies={'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'})

# Start the ZAP scan
print(f'Starting ZAP scan for {target_url}')
scan_id = zap.spider.scan(target_url)

# Wait for the spider to complete
while (int(zap.spider.status(scan_id)) < 100):
    print(f'Spider progress: {zap.spider.status(scan_id)}%')
    time.sleep(1)

print('Spider finished.')

# Start the active scan
print('Starting active scan...')
ascan_id = zap.ascan.scan(target_url)
while (int(zap.ascan.status(ascan_id)) < 100):
    print(f'Active scan progress: {zap.ascan.status(ascan_id)}%')
    time.sleep(5)

print('Active scan finished.')

# Print the results
print('Scan Results:')
for alert in zap.core.alerts():
    print(f'  - {alert["alert"]} ({alert["risk"]})')
