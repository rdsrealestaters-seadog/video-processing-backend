from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

# -------------------------------
# Health check (optional but useful)
# -------------------------------
@app.route("/", methods=["GET"])
def home():
    return "Server is running"

# -------------------------------
# TRANSCRIBE ENDPOINT (THIS IS WHAT YOU WERE MISSING)
# -------------------------------
@app.route("/transcribe", methods=["POST"])
def transcribe():
    data = request.get_json()

    if not data or "file_url" not in data:
        return jsonify({"error": "Missing file_url"}), 400

    file_url = data["file_url"]

    print("Received file URL:", file_url)

    # Right now we are NOT processing yet
    # We are just confirming pipeline works

    return jsonify({
        "status": "received",
        "file_url": file_url
    })


# -------------------------------
# RUN SERVER
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
