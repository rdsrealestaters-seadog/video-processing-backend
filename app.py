from flask import Flask, request, jsonify
import os
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

    if not data or "file_url" not in data:
        return jsonify({"error": "Missing file_url"}), 400

    file_url = data["file_url"]
    job_id = str(uuid.uuid4())

    JOBS[job_id] = {
        "status": "queued",
        "file_url": file_url,
        "video_path": None,
        "audio_path": None,
        "error": None
    }

    thread = threading.Thread(target=process_video_job, args=(job_id, file_url), daemon=True)
    thread.start()

    return jsonify({
        "status": "accepted",
        "job_id": job_id,
        "check_status_url": f"/jobs/{job_id}"
    }), 202


@app.route("/jobs/<job_id>", methods=["GET"])
def get_job(job_id):
    job = JOBS.get(job_id)

    if not job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify(job), 200


def process_video_job(job_id, file_url):
    job_dir = os.path.join(WORKDIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    video_path = os.path.join(job_dir, "input_video.mp4")
    audio_path = os.path.join(job_dir, "audio.mp3")

    try:
        JOBS[job_id]["status"] = "downloading"

        download_file(file_url, video_path)
        JOBS[job_id]["video_path"] = video_path

        JOBS[job_id]["status"] = "extracting_audio"

        extract_audio(video_path, audio_path)
        JOBS[job_id]["audio_path"] = audio_path

        JOBS[job_id]["status"] = "complete"

    except Exception as e:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)


def download_file(url, output_path):
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)


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
