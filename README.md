# Future Vision Generator

An AI-powered web application that helps users visualize their dreams and aspirations through personalized video generation.

## Features

- Interactive Vision Advisor that guides you through exploring your dreams
- Custom video generation based on your vision
- Photo integration to personalize the experience
- Download generated videos

## Technologies Used

- Flask (Python web framework)
- OpenAI GPT-4 for natural conversation
- Replicate API for video generation
- HTML/CSS/JavaScript for frontend

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/future-vision-app.git
cd future-vision-app
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your API keys:
```
OPENAI_API_KEY=your_openai_api_key
REPLICATE_API_TOKEN=your_replicate_api_token
```

5. Run the application:
```bash
python app.py
```

Visit `http://localhost:5002` in your browser to start using the app.

## Usage

1. Start a conversation with the Vision Advisor
2. Answer three questions about your dreams and aspirations
3. Upload a photo (optional)
4. Generate a personalized video of your vision
5. Download and share your vision video

## License

MIT License - feel free to use and modify for your own projects!
