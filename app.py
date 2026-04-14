from flask import Flask, request, jsonify
import os
import re
import uuid
import threading
import subprocess
import requests

app = Flask(__name__)

JOBS = {}
WORKDIR = "/tmp/video_jobs"
os.makedirs(WORKDIR, exist_ok=True)


@app.route("/", methods=["GET"])
def home():
    return "Server is running"


@app.route("/transcribe", methods=["POST"])
def transcribe():
    data = request.get_json(silent=True)

    if not data or "file_id" not in data:
        return jsonify({"error": "Missing file_id"}), 400

    file_id = data["file_id"]
    file_name = data.get("file_name", "input_video.mp4")
    job_id = str(uuid.uuid4())

    JOBS[job_id] = {
        "status": "queued",
        "file_id": file_id,
        "file_name": file_name,
        "video_path": None,
        "audio_path": None,
        "transcript": None,
        "error": None
    }

    thread = threading.Thread(
        target=process_video_job,
        args=(job_id, file_id, file_name),
        daemon=True
    )
    thread.start()

    return jsonify({
        "status": "accepted",
        "job_id": job_id,
        "check_status_url": f"https://video-processing-backend-5z0e.onrender.com/jobs/{job_id}"
    }), 202


@app.route("/jobs/<job_id>", methods=["GET"])
def get_job(job_id):
    job = JOBS.get(job_id)

    if not job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify(job), 200


def process_video_job(job_id, file_id, file_name):
    job_dir = os.path.join(WORKDIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    safe_name = sanitize_filename(file_name)
    if not safe_name.lower().endswith((".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv")):
        safe_name = safe_name + ".mp4"

    video_path = os.path.join(job_dir, safe_name)
    audio_path = os.path.join(job_dir, "audio.mp3")

    try:
        JOBS[job_id]["status"] = "downloading"
        download_google_drive_file(file_id, video_path)
        JOBS[job_id]["video_path"] = video_path

        JOBS[job_id]["status"] = "extracting_audio"
        extract_audio(video_path, audio_path)
        JOBS[job_id]["audio_path"] = audio_path

        JOBS[job_id]["status"] = "transcribing"
        JOBS[job_id]["transcript"] = f"Audio extracted successfully from Google Drive file_id {file_id}"

        JOBS[job_id]["status"] = "complete"

    except Exception as e:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)


def sanitize_filename(name):
    name = os.path.basename(name)
    return re.sub(r'[^A-Za-z0-9._-]+', '_', name)


def download_google_drive_file(file_id, output_path):
    session = requests.Session()
    base_url = "https://drive.google.com/uc?export=download"

    response = session.get(
        base_url,
        params={"id": file_id},
        stream=True,
        timeout=300
    )
    response.raise_for_status()

    confirm_token = get_confirm_token(response)

    if confirm_token:
        response.close()
        response = session.get(
            base_url,
            params={"id": file_id, "confirm": confirm_token},
            stream=True,
            timeout=300
        )
        response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if "text/html" in content_type.lower():
        preview = response.text[:500]
        raise RuntimeError(
            "Google Drive did not return a direct file download. "
            "Make sure the file is shared so Render can access it. "
            f"Preview: {preview}"
        )

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            return value
    return None


def extract_audio(video_path, audio_path):
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
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
