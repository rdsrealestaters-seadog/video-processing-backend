from flask import Flask, request, jsonify
import threading
import subprocess
import requests
import os

app = Flask(__name__)

def extract_audio_from_file(video_path):
    try:
        audio_path = os.path.splitext(video_path)[0] + ".mp3"

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

def download_and_extract(file_url, file_name):
    try:
        video_path = f"/tmp/{file_name}"

        response = requests.get(file_url, stream=True)
        response.raise_for_status()

        with open(video_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        extract_audio_from_file(video_path)

    except Exception as e:
        print(f"Background download processing failed: {e}")

@app.route("/")
def home():
    return "Backend is running"

@app.route("/process", methods=["POST"])
def process():
    try:
        # Path 1: actual uploaded file
        if "file" in request.files:
            uploaded_file = request.files["file"]
            file_name = request.form.get("file_name") or uploaded_file.filename

            if not file_name:
                return jsonify({"error": "Missing file_name"}), 400

            video_path = f"/tmp/{file_name}"
            uploaded_file.save(video_path)

            thread = threading.Thread(target=extract_audio_from_file, args=(video_path,))
            thread.start()

            return jsonify({
                "status": "received",
                "message": "Uploaded file received and processing started",
                "file_name": file_name
            }), 200

        # Path 2: JSON with URL
        data = request.get_json(silent=True)
        if data:
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
                "message": "URL received and processing started",
                "file_name": file_name
            }), 200

        return jsonify({"error": "No valid file upload or JSON body received"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
