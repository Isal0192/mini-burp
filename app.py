from flask import Flask, render_template, request, jsonify
import requests
import dns.resolver
from urllib.parse import urljoin
import concurrent.futures
import os
import signal
import json
import sys
import re
import subprocess

# --- Absolute Path Configuration ---

APP_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(APP_DIR, 'templates')
STATIC_DIR = os.path.join(APP_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

PROXY_LOG_FILE = os.path.join(APP_DIR, 'proxy_log.json')
SUBDOMAINS_FILE = os.path.join(APP_DIR, 'subdomains.txt') # Keeping for now if needed later, or remove
WORDLISTS_DIR = os.path.join(APP_DIR, 'wordlists')
VERSION_FILE = os.path.join(APP_DIR, 'version.txt')
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/Isal0192/mini-burp/main/version.txt"

# --- Update System Routes ---
@app.route('/check-update')
def check_update():
    try:
        # Get local version
        local_version = "Unknown"
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, 'r') as f:
                local_version = f.read().strip()
        
        # Get remote version
        response = requests.get(GITHUB_VERSION_URL, timeout=5)
        if response.status_code == 200:
            remote_version = response.text.strip()
            
            # Simple string comparison (for now)
            # In a real app, use semantic versioning parsing
            update_available = remote_version != local_version
            
            return jsonify({
                "status": "success",
                "local": local_version,
                "remote": remote_version,
                "update_available": update_available
            })
        else:
            return jsonify({"status": "error", "message": "Failed to fetch remote version."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/do-update', methods=['POST'])
def do_update():
    try:
        # Run git pull
        result = subprocess.run(['git', 'pull'], cwd=APP_DIR, capture_output=True, text=True)
        if result.returncode == 0:
            return jsonify({"status": "success", "message": "Update successful! Please restart miniburps."})
        else:
            return jsonify({"status": "error", "message": f"Git pull failed: {result.stderr}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# --- Main App Routes ---
@app.route('/')
def index():
    return render_template('index.html')

# --- Proxy Routes ---
@app.route('/proxy')
def proxy_page():
    return render_template('proxy.html')

# --- Decoder Routes ---
@app.route('/decoder')
def decoder_page():
    return render_template('decoder.html')

@app.route('/get-proxy-logs', methods=['GET'])
def get_proxy_logs():
    if not os.path.exists(PROXY_LOG_FILE):
        return jsonify([])
    logs = []
    try:
        with open(PROXY_LOG_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
        return jsonify(logs)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading proxy log file: {e}", file=sys.stderr)
        return jsonify(logs)

@app.route('/clear-proxy-logs', methods=['POST'])
def clear_proxy_logs():
    try:
        with open(PROXY_LOG_FILE, 'w') as f:
            f.write('')
        return jsonify({"status": "success", "message": "Proxy logs cleared."})
    except IOError as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def _parse_curl_command(curl_command):
    method = "GET"
    url = ""
    headers = {}
    data = None
    
    # Remove 'curl ' prefix if present
    if curl_command.strip().startswith("curl "):
        curl_command = curl_command.strip()[5:].strip()

    # Split command by spaces, respecting quotes
    import shlex
    try:
        parts = shlex.split(curl_command)
    except ValueError as e:
        return None, None, None, None, {"error": f"Error parsing cURL command: {e}"}

    i = 0
    while i < len(parts):
        part = parts[i]
        if part == "-X" or part == "--request":
            if i + 1 < len(parts):
                method = parts[i+1].upper()
                i += 1
        elif part == "-H" or part == "--header":
            if i + 1 < len(parts):
                header_pair = parts[i+1]
                if ':' in header_pair:
                    key, value = header_pair.split(':', 1)
                    headers[key.strip()] = value.strip()
                i += 1
        elif part == "-d" or part.startswith("--data"):
            if i + 1 < len(parts):
                data = parts[i+1]
                # If method is still GET and data is present, assume POST
                if method == "GET":
                    method = "POST"
                i += 1
            else: # If -d or --data is last argument
                data = ""
                if method == "GET":
                    method = "POST"
        elif not part.startswith('-'): # Assume it's the URL
            # Only set URL if not already set, or if it looks more like a URL
            # This prioritizes the last non-flag argument as URL
            if not url or part.startswith('http'):
                url = part
        i += 1

    # If data is present and Content-Type is not set, set to application/x-www-form-urlencoded
    if data and method == "POST" and "Content-Type" not in headers and "content-type" not in headers:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        # Check if data looks like JSON, if so, change Content-Type
        try:
            json.loads(data)
            headers["Content-Type"] = "application/json"
        except (json.JSONDecodeError, TypeError):
            pass # Not JSON, keep as form-urlencoded or whatever was set

    if not url:
        return None, None, None, None, {"error": "URL not found in cURL command."}

    return method, url, headers, data, None

@app.route('/parse-curl', methods=['POST'])
def parse_curl_command_route():
    data = request.get_json()
    curl_command = data.get('curl_command')

    if not curl_command:
        return jsonify({"error": "cURL command is missing."}), 400

    method, url, headers, body, error = _parse_curl_command(curl_command)

    if error:
        return jsonify(error), 400

    # Construct raw HTTP request string
    request_lines = [f"{method} {url} HTTP/1.1"]
    
    # Automatically add Host header if not already present
    host_header_present = False
    for k in headers:
        if k.lower() == 'host':
            host_header_present = True
            break
            
    if not host_header_present:
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            if parsed_url.netloc:
                request_lines.append(f"Host: {parsed_url.netloc}")
        except Exception as e:
            print(f"Error parsing URL for Host header: {e}", file=sys.stderr)
            # If URL parsing fails, don't add Host header, let the user manually add if needed

    for key, value in headers.items():
        request_lines.append(f"{key}: {value}")

    raw_request = "\n".join(request_lines)
    if body:
        raw_request += f"\n\n{body}"
    else:
        raw_request += "\n\n" # Ensure there's a double newline even for no body

    return jsonify({"raw_request": raw_request})

# --- Repeater Routes ---
@app.route('/repeater')
def repeater_page():
    return render_template('repeater.html')


# --- Fuzzer Routes ---
@app.route('/fuzzer')
def fuzzer_page():
    raw_request = request.args.get('request', '')
    return render_template('fuzzer.html', raw_request=raw_request)

@app.route('/fuzzer/run', methods=['POST'])
def run_fuzzer():
    # Use request.form for multipart form data
    raw_request = request.form.get('raw_request')
    payload_type = request.form.get('payload_type')
    grep_string = request.form.get('grep_string')

    if not raw_request or '§' not in raw_request:
        return jsonify({"error": "Raw request with payload marker §...§ is required."}), 400

    payloads = []
    if payload_type == 'numbers':
        try:
            start_val = int(request.form.get('start'))
            end_val = int(request.form.get('end'))
            step_val = int(request.form.get('step', 1))
            if step_val <= 0: step_val = 1
            payloads = range(start_val, end_val + 1, step_val)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid number range specified."}), 400
    
    elif payload_type == 'wordlist':
        if 'wordlist' not in request.files:
            return jsonify({"error": "Wordlist file not provided."}), 400
        
        wordlist_file = request.files['wordlist']
        if wordlist_file.filename == '':
            return jsonify({"error": "No selected file."}), 400
            
        try:
            # Read file content securely
            wordlist_content = wordlist_file.read().decode('utf-8', errors='ignore')
            payloads = wordlist_content.strip().split('\n')
        except Exception as e:
            return jsonify({"error": f"Failed to read wordlist file: {e}"}), 500
            
    elif payload_type == 'builtin':
        wordlist_name = request.form.get('wordlist_name')
        if not wordlist_name:
            return jsonify({"error": "No wordlist selected."}), 400
        
        file_path = os.path.join(WORDLISTS_DIR, wordlist_name)
        # Security check to prevent path traversal
        if not os.path.abspath(file_path).startswith(os.path.abspath(WORDLISTS_DIR)):
             return jsonify({"error": "Invalid wordlist path."}), 400
             
        if not os.path.exists(file_path):
             return jsonify({"error": "Wordlist file not found."}), 404
             
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                payloads = [line.strip() for line in f if line.strip()]
        except Exception as e:
             return jsonify({"error": f"Failed to read built-in wordlist: {e}"}), 500
    
    else:
        return jsonify({"error": "Invalid payload type."}), 400

    results = []
    # Using ThreadPoolExecutor for concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_payload = {
            executor.submit(send_fuzz_request, raw_request, str(p), grep_string): p 
            for p in payloads
        }
        for future in concurrent.futures.as_completed(future_to_payload):
            payload = future_to_payload[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                results.append({"payload": payload, "status": "Exception", "length": 0, "match": False})
    
    # Sort results by payload if it's numeric, otherwise keep original order
    try:
        results.sort(key=lambda x: int(x['payload']))
    except (ValueError, TypeError):
        pass # Keep original order for non-numeric payloads

    return jsonify(results)

@app.route('/get-wordlists')
def get_wordlists():
    if not os.path.exists(WORDLISTS_DIR):
        return jsonify([])
    try:
        files = [f for f in os.listdir(WORDLISTS_DIR) if os.path.isfile(os.path.join(WORDLISTS_DIR, f))]
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500



def send_fuzz_request(raw_request, payload, grep_string):
    """Helper function to send a single fuzzed request."""
    # Replace only the first occurrence of the marker
    fuzzed_request_str = re.sub(r'§.*?§', payload, raw_request, 1)
    
    method, full_url, headers, body, _, error = _parse_raw_request(fuzzed_request_str)
    
    if error:
        return {"payload": payload, "status": "Parse Error", "length": 0, "match": False}
        
    try:
        response = requests.request(method, full_url, headers=headers, data=body, timeout=7, verify=False, allow_redirects=False)
        match_found = bool(grep_string and grep_string in response.text)
        return {"payload": payload, "status": response.status_code, "length": len(response.content), "match": match_found}
    except requests.RequestException:
        return {"payload": payload, "status": "Request Error", "length": 0, "match": False}


def _parse_raw_request(raw_request):
    try:
        header_part, body_part = raw_request.split('\n\n', 1)
    except ValueError:
        header_part = raw_request.strip()
        body_part = None
    request_lines = header_part.strip().split('\n')
    first_line = request_lines.pop(0)
    method, path, _ = first_line.split(' ')
    headers = {k.strip(): v.strip() for k, v in (line.split(':', 1) for line in request_lines if ':' in line)}
    host = headers.get('Host') or headers.get('host')
    if not host:
        return None, None, None, None, None, {"error": "Host header not found."}
    scheme = 'https' if headers.get('Upgrade-Insecure-Requests') != '1' and not headers.get('X-Forwarded-Proto') == 'http' else 'http'
    base_url = f"{scheme}://{host}"
    full_url = urljoin(base_url, path)
    return method, full_url, headers, body_part, path, None

@app.route('/send-single-request', methods=['POST'])
def send_single_request():
    data = request.get_json()
    raw_request = data.get('raw_request')
    if not raw_request:
        return jsonify({"error": "Raw request is missing."}),
        
    method, full_url, headers, body, _, error = _parse_raw_request(raw_request)
    if error:
        return jsonify(error),
        
    try:
        response = requests.request(method, full_url, headers=headers, data=body, timeout=10, verify=False, allow_redirects=True)
        return jsonify({"status_code": response.status_code, "headers": dict(response.headers), "body": response.text})
    except requests.RequestException as e:
        return jsonify({"error": str(e)}),

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')