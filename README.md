# 🎓 AI Personalized Learning Coach

## Project Overview

The AI Personalized Learning Coach is a web application built with Python and Streamlit that helps learners create personalized study plans, practice quizzes, understand their results, and track their learning progress.

The application uses Google Gemini to generate AI-powered learning content and SQLite to store learner information and progress.

## Features

- **Learner Profile:** Enter your name, subject, learning level, goals, and available study time.
- **Personalized Learning Plans:** Generate study plans using Google Gemini.
- **Practice Quizzes:** Generate quizzes to test your understanding.
- **Automatic Scoring:** Calculate quiz scores using Python.
- **Answer Explanations:** Review explanations for quiz results.
- **Progress Dashboard:** View learning history and progress charts.
- **Saved Learning Plans:** Download your learning plans.
- **Database Storage:** Store learner profiles and progress using SQLite.
- **Single-Page Interface:** Access the main learning features from one page.

## Technologies Used

- Python
- Streamlit
- Google Gemini API
- SQLite
- Pandas and data-visualization libraries
- python-dotenv

## Requirements

- Python installed on your computer
- A Google Gemini API key
- Internet access for AI-powered features

## Installation and Setup

### 1. Clone or download the project

Open a terminal in the project folder.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment on Windows

```cmd
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 5. Configure your API key

Create a `.env` file in the project folder and add your Gemini API key:

```text
GEMINI_API_KEY=your_actual_api_key
```

Replace `your_actual_api_key` with your own key. **Never upload your `.env` file or share your API key publicly.**

### 6. Run the application

```bash
python -m streamlit run app.py
```

Streamlit will display a local URL, usually `http://localhost:8501`. Open it in your browser.

## Project Structure

```text
ai-personalized-learning-coach/
├── app.py
├── ai_service.py
├── database.py
├── learning_plan.py
├── quiz_manager.py
├── requirements.txt
├── README.md
├── .gitignore
└── .env
```

The exact project files may vary depending on your implementation.

## Security

- Keep API keys in environment variables.
- Do not commit `.env` or `.venv/` to Git.
- Keep local database files out of public repositories if they contain personal information.

## Future Improvements

- More personalized learning recommendations
- Additional quiz formats and difficulty levels
- Improved progress analytics
- Support for additional AI providers

## Author

Developed as an AI-powered learning assistance project.
