from flask import Flask, request, jsonify
import os
import openai

app = Flask(__name__)

# Set your OpenAI API key in environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/gen", methods=["GET"])
def generate_images_api():
    prompt = request.args.get("prompt")
    if not prompt:
        return jsonify({"success": False, "error": "Missing 'prompt' parameter"}), 400

    num_images = int(request.args.get("num", 2))

    try:
        response = openai.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            n=num_images
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    # Format images as list of objects with id and url
    images = [{"id": idx + 1, "url": img["url"]} for idx, img in enumerate(response.data)]

    # Use a random job_id (or timestamp) since OpenAI doesn't provide one
    import uuid
    job_id = str(uuid.uuid4())

    return jsonify({
        "success": True,
        "prompt": prompt,
        "job_id": job_id,
        "images": images
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
