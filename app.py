from flask import Flask, request, jsonify
import requests
import os
import subprocess

app = Flask(__name__)

@app.route("/")
def home():
    return "Backend is running"

@app.route("/process", methods=["POST"])
def process():
    data = request.json
    file_url = data.get("file_url")
    file_name = data.get("file_name")

    if not file_url:
        return jsonify({"error": "No file URL provided"}), 400

    try:
        # Download file
        response = requests.get(file_url)
        file_path = f"/tmp/{file_name}"

        with open(file_path, "wb") as f:
            f.write(response.content)

        # Extract audio using ffmpeg
        audio_path = file_path.replace(".mp4", ".mp3")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", file_path,
            "-vn",
            "-acodec", "mp3",
            audio_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return jsonify({
                "status": "error",
                "stage": "audio_extraction",
                "message": result.stderr
            }), 500

        return jsonify({
            "status": "audio_extracted",
            "video_file": file_path,
            "audio_file": audio_path
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
