import json
import time
import sys
import os
from mitmproxy import http

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(APP_DIR, 'proxy_log.json')

class ProxyLogger:
    def __init__(self):
        # Clear the log file on start
        try:
            with open(LOG_FILE, 'w') as f:
                f.write('') # Write empty to clear it
        except IOError:
            pass # Ignore if file doesn't exist yet

    def request(self, flow: http.HTTPFlow) -> None:
        """
        The full HTTP request has been read.
        """
        request_data = {
            'id': str(flow.id),
            'timestamp': time.time(),
            'method': flow.request.method,
            'url': flow.request.url,
            'headers': dict(flow.request.headers),
            'content': flow.request.get_text(),
        }

        # Append a new JSON line to the log file and flush it
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(json.dumps(request_data) + '\n')
                f.flush() # Force write to disk immediately
        except IOError as e:
            print(f"Error writing to log file: {e}", file=sys.stderr)

addons = [
    ProxyLogger()
]
