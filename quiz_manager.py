from ai_service import generate_json, AIServiceError


def generate_quiz(
    subject,
    topic,
    current_level,
    num_questions=5,
):
    """Generate and validate a multiple-choice quiz."""

    if not isinstance(subject, str) or not subject.strip():
        raise AIServiceError("Please provide a valid quiz subject.")

    if not isinstance(topic, str) or not topic.strip():
        raise AIServiceError("Please provide a valid quiz topic.")

    if current_level not in ("Beginner", "Intermediate", "Advanced"):
        raise AIServiceError("Please select a valid difficulty level.")

    if (
        not isinstance(num_questions, int)
        or isinstance(num_questions, bool)
        or num_questions not in (5, 10)
    ):
        raise AIServiceError("Choose either 5 or 10 quiz questions.")

    prompt = f"""
Create a multiple-choice quiz for a learner.

Subject: {subject.strip()}
Topic: {topic.strip()}
Difficulty: {current_level}
Number of questions: {num_questions}

Return valid JSON with this structure:
{{
    "title": "Quiz title",
    "subject": "{subject.strip()}",
    "topic": "{topic.strip()}",
    "questions": [
        {{
            "id": 1,
            "question": "Question text",
            "options": {{
                "A": "First option",
                "B": "Second option",
                "C": "Third option",
                "D": "Fourth option"
            }},
            "correct_answer": "A",
            "explanation": "Explain why the answer is correct",
            "difficulty": "{current_level}"
        }}
    ]
}}

Generate exactly {num_questions} unique questions.
Every question needs four non-empty options, one correct answer,
a clear explanation, and a unique integer ID starting at 1.
Return valid JSON only, without Markdown fences.
"""

    try:
        result = generate_json(prompt)

    except AIServiceError:
        # Local backup quiz when Gemini is unavailable.
        result = {
            "title": f"{topic} Practice Quiz (Backup — Not AI-Generated)",
            "subject": subject.strip(),
            "topic": topic.strip(),
            "questions": [
                {
                    "id": i,
                    "question": (
                        f"General study-skills question {i}: "
                        "Which approach best checks understanding "
                        "of a new concept?"
                    ),
                    "options": {
                        "A": "Apply the concept to an example",
                        "B": "Skip practice completely",
                        "C": "Memorize words without understanding",
                        "D": "Avoid reviewing mistakes",
                    },
                    "correct_answer": "A",
                    "explanation": (
                        "Applying a concept to an example helps check "
                        "understanding. This is a generic backup question, "
                        "not a subject-specific question."
                    ),
                    "difficulty": current_level,
                }
                for i in range(1, num_questions + 1)
            ],
        }

    # Validate both AI-generated and backup quizzes.
    if not isinstance(result, dict):
        raise AIServiceError("The quiz has an invalid format.")

    questions = result.get("questions")

    if (
        not isinstance(questions, list)
        or len(questions) != num_questions
    ):
        raise AIServiceError(
            f"The quiz must contain exactly {num_questions} questions."
        )

    seen_ids = set()
    required_fields = (
        "question",
        "options",
        "correct_answer",
        "explanation",
    )

    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            raise AIServiceError(f"Question {index} has an invalid format.")

        for field in required_fields:
            if field not in question:
                raise AIServiceError(
                    f"Question {index} is missing '{field}'."
                )

        if (
            not isinstance(question["question"], str)
            or not question["question"].strip()
        ):
            raise AIServiceError(f"Question {index} has empty question text.")

        if (
            not isinstance(question["explanation"], str)
            or not question["explanation"].strip()
        ):
            raise AIServiceError(f"Question {index} has an empty explanation.")

        options = question["options"]
        if not isinstance(options, dict) or set(options) != {
            "A", "B", "C", "D"
        }:
            raise AIServiceError(
                f"Question {index} must contain options A, B, C, and D."
            )

        if any(
            not isinstance(options[key], str) or not options[key].strip()
            for key in ("A", "B", "C", "D")
        ):
            raise AIServiceError(f"Question {index} has an empty option.")

        if question["correct_answer"] not in ("A", "B", "C", "D"):
            raise AIServiceError(
                f"Question {index} has an invalid correct answer."
            )

        question_id = question.get("id", index)
        if (
            not isinstance(question_id, int)
            or isinstance(question_id, bool)
            or question_id in seen_ids
        ):
            raise AIServiceError(
                f"Question {index} has a missing, duplicate, or invalid ID."
            )

        seen_ids.add(question_id)
        question["id"] = question_id

    return result
