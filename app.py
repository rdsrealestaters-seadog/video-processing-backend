from flask import Flask, request, jsonify
import os
import re
import uuid
import threading
import subprocess

app = Flask(__name__)

JOBS = {}
WORKDIR = "/tmp/video_jobs"
os.makedirs(WORKDIR, exist_ok=True)


@app.route("/", methods=["GET"])
def home():
    return "Server is running"


@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "file" not in request.files:
        return jsonify({"error": "Missing uploaded file"}), 400

    uploaded_file = request.files["file"]
    file_name = uploaded_file.filename or "input_video.mp4"
    job_id = str(uuid.uuid4())

    JOBS[job_id] = {
        "status": "queued",
        "file_name": file_name,
        "video_path": None,
        "audio_path": None,
        "transcript": None,
        "error": None
    }

    job_dir = os.path.join(WORKDIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    safe_name = sanitize_filename(file_name)
    if not safe_name.lower().endswith((".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv")):
        safe_name = safe_name + ".mp4"

    video_path = os.path.join(job_dir, safe_name)
    uploaded_file.save(video_path)
    JOBS[job_id]["video_path"] = video_path

    thread = threading.Thread(
        target=process_video_job,
        args=(job_id, video_path),
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


def process_video_job(job_id, video_path):
    job_dir = os.path.dirname(video_path)
    audio_path = os.path.join(job_dir, "audio.mp3")

    try:
        JOBS[job_id]["status"] = "extracting_audio"
        extract_audio(video_path, audio_path)
        JOBS[job_id]["audio_path"] = audio_path

        JOBS[job_id]["status"] = "transcribing"
        JOBS[job_id]["transcript"] = f"Audio extracted successfully from uploaded file {os.path.basename(video_path)}"

        JOBS[job_id]["status"] = "complete"

    except Exception as e:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)


def sanitize_filename(name):
    name = os.path.basename(name)
    return re.sub(r'[^A-Za-z0-9._-]+', '_', name)


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
