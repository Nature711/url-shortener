from flask import Flask, jsonify, request
import string
import os

app = Flask(__name__)

# Storage files
COUNTER_FILE = "v1/counter.txt"
MAPPING_FILE = "v1/url_mapping.txt"

# Base62 characters
BASE62_CHARS = string.digits + string.ascii_letters  # "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

# Load existing URL mappings into memory
url_mapping = {}

# Check if MAPPING_FILE exists, if not, create it
if not os.path.exists(MAPPING_FILE):
    with open(MAPPING_FILE, "w") as f:
        # Create an empty mapping file if it doesn't exist
        pass
else:
    with open(MAPPING_FILE, "r") as f:
        for line in f:
            short_url, long_url = line.strip().split(",", 1)
            url_mapping[short_url] = long_url

# Check if COUNTER_FILE exists, if not, create it and initialize to 1
if not os.path.exists(COUNTER_FILE):
    with open(COUNTER_FILE, "w") as f:
        f.write("1")  # Initialize counter to 1
else:
    with open(COUNTER_FILE, "r") as f:
        counter = int(f.read().strip())

def encode_base62(num):
    """Converts a base-10 number to base-62 string."""
    if num == 0:
        return BASE62_CHARS[0]

    base62 = []
    while num:
        num, remainder = divmod(num, 62)
        base62.append(BASE62_CHARS[remainder])

    return ''.join(reversed(base62))

@app.route("/create", methods=["POST"])
def create_short_url():
    global counter

    long_url = request.args.get("long_url")
    if not long_url:
        return jsonify({"error": "Missing long_url parameter"}), 400

    # Check if the long URL already exists
    for short_url, stored_url in url_mapping.items():
        if stored_url == long_url:
            return jsonify({"short_url": short_url, "long_url": long_url})

    # Generate new short URL
    short_url = encode_base62(counter)
    url_mapping[short_url] = long_url

    # Persist mapping to file
    with open(MAPPING_FILE, "a") as f:
        f.write(f"{short_url},{long_url}\n")

    # Increment and save counter
    counter += 1
    with open(COUNTER_FILE, "w") as f:
        f.write(str(counter))

    return jsonify({"short_url": short_url, "long_url": long_url})

@app.route("/get", methods=["GET"])
def get_long_url():
    short_url = request.args.get("short_url")
    if not short_url or short_url not in url_mapping:
        return jsonify({"error": "Short URL not found"}), 404

    return jsonify({"long_url": url_mapping[short_url]})

if __name__ == "__main__":
    app.run(debug=True, port=5001)
