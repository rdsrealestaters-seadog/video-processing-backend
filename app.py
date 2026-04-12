from flask import Flask, request, jsonify
import os
import subprocess

app = Flask(__name__)

@app.route("/")
def home():
    return "Backend is running"

@app.route("/process", methods=["POST"])
def process():
    try:
        # Get file from multipart form-data
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        uploaded_file = request.files["file"]
        file_name = uploaded_file.filename
        file_path = f"/tmp/{file_name}"

        # Save uploaded file
        uploaded_file.save(file_path)

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
