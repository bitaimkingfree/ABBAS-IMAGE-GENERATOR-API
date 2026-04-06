from flask import Flask, request, jsonify
import requests
import time
import json

app = Flask(__name__)

BASE_URL = "https://genpick.app"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Accept": "application/json"  # No streaming for serverless
}

MAX_RETRIES = 15
RETRY_DELAY = 2  # seconds


def create_job(prompt, num_images=2, aspect="1:1", style="diversity"):
    url = f"{BASE_URL}/api/imagen?async=true"
    payload = {
        "prompt": prompt,
        "aspectRatio": aspect,
        "numberOfImages": num_images,
        "style": style
    }
    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        return data.get("jobId")
    except Exception as e:
        print("Error creating job:", e)
        return None


def fetch_images(job_id):
    url = f"{BASE_URL}/api/imagen/jobs/{job_id}"
    images = []

    for _ in range(MAX_RETRIES):
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code != 200:
                time.sleep(RETRY_DELAY)
                continue
            data = r.json()
            # The API may return images as a list of objects with "imageUrl"
            if isinstance(data, dict) and "images" in data and len(data["images"]) > 0:
                images = [img.get("imageUrl") for img in data["images"] if img.get("imageUrl")]
                if images:
                    break
        except Exception as e:
            print("Error fetching images:", e)
        time.sleep(RETRY_DELAY)

    return images


@app.route("/gen", methods=["GET"])
def generate_images_api():
    prompt = request.args.get("prompt")
    if not prompt:
        return jsonify({"success": False, "error": "Missing 'prompt' parameter"}), 400

    num_images = int(request.args.get("num", 2))
    aspect = request.args.get("aspect", "1:1")
    style = request.args.get("style", "diversity")

    job_id = create_job(prompt, num_images, aspect, style)
    if not job_id:
        return jsonify({"success": False, "error": "Job creation failed"}), 500

    images_urls = fetch_images(job_id)
    if not images_urls:
        return jsonify({"success": False, "error": "No images returned"}), 500

    # Format images as objects with id and url
    images = [{"id": idx + 1, "url": url} for idx, url in enumerate(images_urls)]

    return jsonify({
        "success": True,
        "prompt": prompt,
        "job_id": job_id,
        "images": images
    })


if __name__ == "__main__":
    # Only used when testing locally
    app.run(host="0.0.0.0", port=5000)
