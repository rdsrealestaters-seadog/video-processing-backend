from flask import Flask, request, jsonify
import threading
import subprocess
import os

app = Flask(__name__)

def extract_audio(file_path):
    try:
        audio_path = file_path.replace(".mp4", ".mp3")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", file_path,
            "-vn",
            "-acodec", "mp3",
            audio_path
        ]

        subprocess.run(cmd, capture_output=True, text=True)
    except Exception as e:
        print(f"Audio extraction failed: {e}")

@app.route("/")
def home():
    return "Backend is running"

@app.route("/process", methods=["POST"])
def process():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        uploaded_file = request.files["file"]
        file_name = uploaded_file.filename
        file_path = f"/tmp/{file_name}"

        uploaded_file.save(file_path)

        thread = threading.Thread(target=extract_audio, args=(file_path,))
        thread.start()

        return jsonify({
            "status": "received",
            "video_file": file_path,
            "message": "File received and audio extraction started"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
