from flask import Flask, render_template, request, jsonify, session
import os
import replicate
from dotenv import load_dotenv
import base64
import tempfile
from openai import OpenAI
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Initialize OpenAI client only if API key is available
openai_client = None
if os.getenv('OPENAI_API_KEY'):
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

VISION_QUESTIONS = [
    "If you could achieve anything in life, regardless of limitations, what would be your ultimate dream?",
    "What's a unique way you'd like to make the world better or different?",
    "Picture yourself at your happiest and most fulfilled - what does that moment look like?"
]

def get_vision_advisor_response(messages):
    """Get response from vision advisor."""
    if not openai_client:
        return {"error": "OpenAI API key not configured"}
    
    try:
        # Start the conversation with system message
        if not messages:
            messages = [{
                "role": "system",
                "content": """You are an inspiring Vision Advisor who helps people dream bigger about their future. 
                Guide them through 3 questions that help them imagine their most extraordinary life.
                Keep your responses brief and enthusiastic. Ask one question at a time."""
            }, {
                "role": "assistant",
                "content": "Hello! I'm here to help you envision your most extraordinary future. Close your eyes for a moment and... " + VISION_QUESTIONS[0]
            }]
            return {
                "message": messages[1]["content"],
                "should_generate_prompt": False
            }
        
        # Get the next question index based on number of user messages
        question_index = len([m for m in messages if m["role"] == "user"])
        
        # Ask the next question
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages + [{
                "role": "system",
                "content": f"Acknowledge their response with enthusiasm (just a few words) and ask: {VISION_QUESTIONS[question_index]}"
            }],
            temperature=0.7
        )
        
        return {
            "message": response.choices[0].message.content,
            "should_generate_prompt": False
        }
    except Exception as e:
        print(f"Error getting vision advisor response: {e}")
        return {"error": str(e)}

def generate_vision_prompt(conversation):
    """Generate a detailed video prompt based on the vision conversation."""
    if not openai_client:
        return "Error: OpenAI API key not configured"
    
    try:
        messages = [
            {"role": "system", "content": """Create a cinematic video prompt that brings their vision to life. The prompt should:
            1. Start with the person (who will be in the provided photo)
            2. Describe a specific, powerful moment of achievement
            3. Include rich visual details of the environment
            4. Capture emotional reactions and atmosphere
            5. Include dynamic elements like screens, lighting, or audience reactions
            
            Format the prompt like this example:
            "The person from the photo stands confidently at [specific location], [specific action/achievement happening]. They are [appearance details], as [environmental details]. [Dynamic elements] create atmosphere, while [emotional/reaction details] capture the significance of the moment."
            
            Make it vivid and specific, focusing on one powerful moment rather than a journey."""},
            {"role": "user", "content": f"Create a video prompt based on this vision conversation: {json.dumps(conversation)}"}
        ]
        
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating vision prompt: {e}")
        return str(e)

@app.route('/')
def index():
    session.clear()  # Clear any existing conversation
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400

    # Initialize conversation if not exists
    if 'conversation' not in session:
        session['conversation'] = []
        session['response_count'] = 0

    # Get coach's response
    if user_message.lower() == 'start':
        # Clear any existing conversation for a fresh start
        session['conversation'] = []
        session['response_count'] = 0
    else:
        # Add user message to conversation and increment counter
        session['conversation'].append({"role": "user", "content": user_message})
        session['response_count'] = session.get('response_count', 0) + 1
        print(f"Response count: {session['response_count']}")  # Debug log

    # Check if we've reached 3 responses
    if session.get('response_count', 0) >= 3:
        return jsonify({
            "message": "Thank you for sharing your vision with me. I'm ready to create something extraordinary for you! VISION_COMPLETE",
            "should_generate_prompt": True
        })
    
    # Get next question if we haven't reached 3 responses
    response = get_vision_advisor_response(session['conversation'])
    
    if 'error' in response:
        return jsonify({'error': response['error']}), 500
        
    return jsonify(response)

@app.route('/generate_prompt', methods=['POST'])
def generate_final_prompt():
    if 'conversation' not in session:
        return jsonify({'error': 'No conversation found'}), 400
    
    prompt = generate_vision_prompt(session['conversation'])
    return jsonify({'prompt': prompt})

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
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(base64.b64decode(image_data))
                temp_file.flush()
                with open(temp_file.name, 'rb') as image_file:
                    subject_image = image_file
                    output = replicate.run(
                        "minimax/video-01",
                        input={
                            "mode": "text-to-video",
                            "prompt": prompt,
                            "subject_reference": subject_image,
                            "num_frames": 150,
                            "fps": 25,
                            "width": 1280,
                            "height": 720,
                            "guidance_scale": 7.5,
                            "num_inference_steps": 50
                        }
                    )
                os.unlink(temp_file.name)
        else:
            output = replicate.run(
                "minimax/video-01",
                input={
                    "mode": "text-to-video",
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
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port)
