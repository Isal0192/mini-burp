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

app = Flask(__name__)

# --- Absolute Path Configuration ---

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROXY_LOG_FILE = os.path.join(APP_DIR, 'proxy_log.json')
SUBDOMAINS_FILE = os.path.join(APP_DIR, 'subdomains.txt') # Keeping for now if needed later, or remove
WORDLISTS_DIR = os.path.join(APP_DIR, 'wordlists')

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