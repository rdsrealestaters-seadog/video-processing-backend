from flask import Flask, request, jsonify
import threading
import subprocess
import requests
import os

app = Flask(__name__)

def download_and_extract(file_url, file_name):
    try:
        video_path = f"/tmp/{file_name}"
        audio_path = video_path.rsplit(".", 1)[0] + ".mp3"

        response = requests.get(file_url, stream=True)
        response.raise_for_status()

        with open(video_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "mp3",
            audio_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print("FFmpeg failed:")
            print(result.stderr)
        else:
            print(f"Audio extracted successfully: {audio_path}")

    except Exception as e:
        print(f"Background processing failed: {e}")

@app.route("/")
def home():
    return "Backend is running"

@app.route("/process", methods=["POST"])
def process():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON received"}), 400

        file_url = data.get("file_url")
        file_name = data.get("file_name")

        if not file_url or not file_name:
            return jsonify({"error": "Missing file_url or file_name"}), 400

        thread = threading.Thread(
            target=download_and_extract,
            args=(file_url, file_name)
        )
        thread.start()

        return jsonify({
            "status": "received",
            "message": "Processing started"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
