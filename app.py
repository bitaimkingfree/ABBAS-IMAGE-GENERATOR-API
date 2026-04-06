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
    try:
        r = requests.post(url, headers=HEADERS, json=payload)
        r.raise_for_status()
        data = r.json()
        return data.get("jobId")
    except Exception as e:
        print("❌ Job creation failed:", e)
        return None


def fetch_images(job_id):
    url = f"{BASE_URL}/api/imagen/jobs/{job_id}"
    params = {"stream": "true"}
    images = []

    try:
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
    except Exception as e:
        print("❌ Fetching images failed:", e)

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

    images = fetch_images(job_id)

    return jsonify({
        "success": True,
        "prompt": prompt,
        "job_id": job_id,
        "count": len(images),
        "images": images
    })


# No app.run() needed for Vercel
