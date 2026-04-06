from flask import Flask, request, jsonify
import requests
import json
import uuid
import time

app = Flask(__name__)

BASE_URL = "https://genpick.app"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Accept": "text/event-stream",
    # "Cookie": "session=<your_session_token_here>"  # add if needed
}

# Store jobs temporarily in memory (for demo purposes)
JOBS = {}


def create_genpick_job(prompt, num_images=2, aspect="1:1", style="diversity"):
    url = f"{BASE_URL}/api/imagen?async=true"
    payload = {
        "prompt": prompt,
        "aspectRatio": aspect,
        "numberOfImages": num_images,
        "style": style
    }
    try:
        r = requests.post(url, headers=HEADERS, json=payload)
        r.raise_for_status()
        data = r.json()
        job_id = data.get("jobId")
        return job_id
    except Exception as e:
        print("Job creation failed:", e)
        return None


def fetch_genpick_images(job_id):
    url = f"{BASE_URL}/api/imagen/jobs/{job_id}"
    params = {"stream": "true"}
    images = []

    try:
        with requests.get(url, headers=HEADERS, params=params, stream=True, timeout=30) as r:
            for line in r.iter_lines():
                if not line:
                    continue
                decoded = line.decode("utf-8")
                if decoded.startswith("data:"):
                    try:
                        data = json.loads(decoded.replace("data:", "").strip())
                        if "imageUrl" in data:
                            images.append(data["imageUrl"])
                    except:
                        continue
    except Exception as e:
        print("Fetching images failed:", e)
    return images


@app.route("/create_job", methods=["GET"])
def create_job_api():
    prompt = request.args.get("prompt")
    num_images = int(request.args.get("num", 2))
    aspect = request.args.get("aspect", "1:1")
    style = request.args.get("style", "diversity")

    if not prompt:
        return jsonify({"success": False, "error": "Missing 'prompt' parameter"}), 400

    job_id = create_genpick_job(prompt, num_images, aspect, style)
    if not job_id:
        return jsonify({"success": False, "error": "Job creation failed"}), 500

    # Store job info temporarily
    JOBS[job_id] = {"prompt": prompt, "num": num_images, "aspect": aspect, "style": style}

    return jsonify({"success": True, "job_id": job_id})


@app.route("/get_images", methods=["GET"])
def get_images_api():
    job_id = request.args.get("job_id")
    if not job_id or job_id not in JOBS:
        return jsonify({"success": False, "error": "Invalid or missing job_id"}), 400

    images = fetch_genpick_images(job_id)
    return jsonify({
        "success": True,
        "job_id": job_id,
        "count": len(images),
        "images": images
    })
