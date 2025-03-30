# Daily AI Challenge

A Django web application that provides users with daily AI image generation challenges. Users can submit their prompts, generate images using DALL-E, and compete with other users in a fun and engaging way.

## Features

- Daily AI image generation challenges
- User authentication and profiles
- Image generation using DALL-E API
- Challenge system with AI-powered judging
- Leaderboard system
- Beautiful Bootstrap-based UI

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Virtual environment (recommended)

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd daily-ai-challenge
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here
DEBUG=True
```

5. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Create a superuser (optional):
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

8. Visit http://127.0.0.1:8000/ in your browser

## Usage

1. Register a new account or log in
2. View the daily challenge on the home page
3. Submit your prompt to generate an image
4. Challenge other users' submissions
5. View your profile and track your progress
6. Check the leaderboard to see how you rank

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 