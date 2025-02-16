from flask import Flask, render_template, request, jsonify
import os
import replicate
from dotenv import load_dotenv
import base64
import tempfile

load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_video():
    try:
        prompt = request.json.get('prompt')
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        # Handle the subject reference image if provided
        subject_image = None
        if 'image' in request.json and request.json['image']:
            image_data = request.json['image'].split(',')[1]
            # Create a temporary file for the subject reference
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(base64.b64decode(image_data))
                temp_file.flush()
                # Open the file in binary mode for the API
                with open(temp_file.name, 'rb') as image_file:
                    subject_image = image_file
                    # Run the model in text-to-video mode with subject reference
                    output = replicate.run(
                        "minimax/video-01",
                        input={
                            "mode": "text-to-video",  # Explicitly set mode to text-to-video
                            "prompt": prompt,
                            "subject_reference": subject_image,  # Optional character reference
                            "num_frames": 150,
                            "fps": 25,
                            "width": 1280,
                            "height": 720,
                            "guidance_scale": 7.5,
                            "num_inference_steps": 50
                        }
                    )
                # Clean up the temporary file
                os.unlink(temp_file.name)
        else:
            # Run the model in text-to-video mode without subject reference
            output = replicate.run(
                "minimax/video-01",
                input={
                    "mode": "text-to-video",  # Explicitly set mode to text-to-video
                    "prompt": prompt,
                    "num_frames": 150,
                    "fps": 25,
                    "width": 1280,
                    "height": 720,
                    "guidance_scale": 7.5,
                    "num_inference_steps": 50
                }
            )

        return jsonify({'video_url': output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5002)
