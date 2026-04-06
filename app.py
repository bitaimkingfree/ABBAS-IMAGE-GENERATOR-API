from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

BASE_URL = "https://genpick.app"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Accept": "text/event-stream"
}

def create_job(prompt, num_images=2, aspect="1:1", style="diversity"):
    url = f"{BASE_URL}/api/imagen?async=true"
    payload = {
        "prompt": prompt,
        "aspectRatio": aspect,
        "numberOfImages": num_images,
        "style": style
    }
    r = requests.post(url, headers=HEADERS, json=payload)
    data = r.json()
    return data.get("jobId")

def fetch_images(job_id):
    url = f"{BASE_URL}/api/imagen/jobs/{job_id}"
    params = {"stream": "true"}
    images = []

    with requests.get(url, headers=HEADERS, params=params, stream=True) as r:
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
    return images

@app.route("/gen", methods=["GET"])
def generate_images_api():
    prompt = request.args.get("prompt")
    num_images = int(request.args.get("num", 2))
    aspect = request.args.get("aspect", "1:1")
    style = request.args.get("style", "diversity")

    if not prompt:
        return jsonify({"success": False, "error": "Missing 'prompt' parameter"}), 400

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
    app.run(host="0.0.0.0", port=5000)