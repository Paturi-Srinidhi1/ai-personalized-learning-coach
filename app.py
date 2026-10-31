
import json
import streamlit as st

from database import (
    initialize_database,
    save_learner,
    update_learner,
    get_learners,
    save_learning_plan,
    save_quiz_attempt,
    get_quiz_attempts,
    get_learning_plans,
)
from learning_plan import generate_learning_plan
from quiz_manager import generate_quiz


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="AI Personalized Learning Coach",
    page_icon="🎓",
    layout="wide",
)

initialize_database()


# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        max-width: 1250px;
    }

    .hero {
        padding: 28px;
        border-radius: 18px;
        background: linear-gradient(120deg, #14213d, #285a8e);
        color: white;
        margin-bottom: 20px;
    }

    .hero h1 {
        color: white;
    }

    .hero p {
        color: #e8f2ff;
        font-size: 17px;
    }

    div[data-testid="stMetric"] {
        background: rgba(120, 140, 170, 0.08);
        padding: 14px;
        border-radius: 12px;
        border: 1px solid rgba(120, 140, 170, 0.2);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

defaults = {
    "learner_id": None,
    "active_plan": None,
    "active_quiz": None,
    "quiz_result": None,
    "learner_subject": "",
    "learner_goal": "",
    "learner_level": "Beginner",
    "saved_quiz_token": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def parse_json(value, fallback=None):
    """Safely parse JSON stored in the database."""
    try:
        if isinstance(value, str):
            return json.loads(value)
        return value if value is not None else fallback
    except (ValueError, TypeError):
        return fallback


def get_plan_topics(plan):
    """Collect unique topics from a learning plan."""
    topics_found = []

    if not isinstance(plan, dict):
        return topics_found

    for week in plan.get("weekly_plan", []):
        topics = week.get("topics", [])

        if isinstance(topics, str):
            topics = [topics]

        for topic in topics:
            topic = str(topic).strip()

            if topic and topic not in topics_found:
                topics_found.append(topic)

    return topics_found


def calculate_accuracy(score, total):
    if not total:
        return 0.0

    return round((score / total) * 100, 1)


def reset_current_session():
    """Clear current work without deleting saved database history."""
    for key in list(st.session_state.keys()):
        if key.startswith("answer_"):
            del st.session_state[key]

    st.session_state.active_plan = None
    st.session_state.active_quiz = None
    st.session_state.quiz_result = None
    st.session_state.learner_id = None
    st.session_state.learner_subject = ""
    st.session_state.learner_goal = ""
    st.session_state.learner_level = "Beginner"

    st.rerun()


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

with st.sidebar:
    st.title("🎓 Learning Coach")
    st.caption("Starting fresh clears the current session, "
                "not your saved database records.")

    page = st.radio(
        "Navigation",
        [
            "🏠 Home & Profile",
            "🗺️ Learning Plan",
            "🧠 Practice Quiz",
            "📊 Progress Dashboard",
        ],
    )

    st.divider()

    st.markdown("### Your study loop")
    st.write("1. Set a learning goal")
    st.write("2. Generate a plan")
    st.write("3. Practise with quizzes")
    st.write("4. Track your progress")

    st.divider()

    if st.button("↻ Start fresh session", use_container_width=True):
        reset_current_session()

    st.caption(
        "Starting fresh clears the current session, "
        "not your saved database records."
    )


# --------------------------------------------------
# APPLICATION HEADER
# --------------------------------------------------

learner_name = st.session_state.get("learner_name", "")

if not learner_name:
    learner_name = "Learner"

st.markdown(
    f"""
    <div class="hero">
        <h1>🎓 Welcome, {learner_name}!</h1>
        <p>
            Your personal AI assistant for structured learning,
            practice quizzes, and progress tracking.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# LEARNER SUMMARY
# --------------------------------------------------

if st.session_state.learner_id:
    st.subheader("👤 Your Learning Summary")

    summary_col1, summary_col2 = st.columns(2)

    with summary_col1:
        st.metric(
            "Learner",
            st.session_state.get("learner_name", "Learner") or "Learner",
        )
        st.metric(
            "Subject",
            st.session_state.get("learner_subject", "") or "Not set",
        )

    with summary_col2:
        st.metric(
            "Current Level",
            st.session_state.get("learner_level", "Beginner"),
        )
        st.write("**Learning Goal**")
        st.write(
            st.session_state.get("learner_goal", "") or "Not set"
        )

    st.divider()

# --------------------------------------------------
# HOME AND LEARNER PROFILE
# --------------------------------------------------

if True:

    st.header("Create Your Learning Profile")

    st.write(
        "Enter your learning goal to generate a personalized "
        "study plan using AI."
    )

    with st.form("profile_form"):

        col1, col2 = st.columns(2)

        with col1:        
            name = st.text_input(
            "Your Name",
            placeholder="Enter your name",
        )
            subject = st.text_input(
                "Subject or Skill",
                placeholder="Example: HTML, Python, History",
            )

            goal = st.text_input(
                "Learning Goal",
                placeholder="Example: Learn HTML fundamentals",
            )

            level = st.selectbox(
                "Current Level",
                ["Beginner", "Intermediate", "Advanced"],
            )

        with col2:
            duration = st.number_input(
                "Plan Duration (days)",
                min_value=1,
                max_value=365,
                value=30,
            )

            hours = st.number_input(
                "Study Hours Per Day",
                min_value=0.5,
                max_value=12.0,
                value=2.0,
                step=0.5,
            )

        submitted = st.form_submit_button(
            "✨ Generate Personalized Learning Plan",
            type="primary",
            use_container_width=True,
        )

    if submitted:

        if not subject.strip() or not goal.strip():
            st.error("Please enter both the subject and learning goal.")

        else:
            with st.spinner("Generating your personalized plan..."):

                try:
                    daily_minutes = int(hours * 60)

                    plan = generate_learning_plan(
                        subject=subject.strip(),
                        goal=goal.strip(),
                        current_level=level,
                        duration_days=int(duration),
                        daily_minutes=daily_minutes,
                    )

                    existing_id = st.session_state.learner_id
                    learners = get_learners()

                    existing_ids = [
                        learner["id"] for learner in learners
                    ]

                    if existing_id in existing_ids:
                        update_learner(                 
                            existing_id,
                            subject.strip(),
                            goal.strip(),
                            level,
                            int(duration),
                            daily_minutes,
                            name=name.strip(),
                        )
                        learner_id = existing_id

                    else:
                        learner_id = save_learner(
                            subject.strip(),
                            goal.strip(),
                            level,
                            int(duration),
                            daily_minutes,
                            name=name.strip(),
                        )

                    save_learning_plan(
                        learner_id,
                        json.dumps(plan, ensure_ascii=False),
                    )

                    st.session_state.learner_id = learner_id
                    st.session_state.active_plan = plan
                    st.session_state.learner_subject = subject.strip()
                    st.session_state.learner_goal = goal.strip()
                    st.session_state.learner_level = level
                    st.session_state.active_quiz = None
                    st.session_state.quiz_result = None
                    st.session_state.saved_quiz_token = None
                    st.session_state.learner_name = name.strip()

                    st.success("Your learning plan has been saved!")
                    st.rerun()

                except Exception as error:
                    st.error(
                        f"Could not generate your plan: {error}"
                    )

                    st.info(
                        "Check your Gemini API configuration, "
                        "internet connection, and API quota."
                    )

    st.divider()
    st.subheader("What this application offers")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🗺️ Learning Plan")
        st.write(
            "Weekly topics, activities, milestones, "
            "and a daily study routine."
        )

    with col2:
        st.markdown("### 🧠 AI Quizzes")
        st.write(
            "Generate quizzes, check your answers, "
            "and learn from explanations."
        )

    with col3:
        st.markdown("### 📊 Progress Tracking")
        st.write(
            "Monitor scores, topic accuracy, "
            "and your learning history."
        )

if True:
    st.header("🗺️ Your Personalized Learning Plan")

    plan = st.session_state.get("active_plan")
    learner_id = st.session_state.get("learner_id")

    # If no plan is active, load the latest saved plan.
    if plan is None and learner_id:
        saved_plans = get_learning_plans(learner_id)
        if saved_plans:
            try:
                plan = json.loads(saved_plans[0]["plan_json"])
                st.session_state.active_plan = plan
            except (json.JSONDecodeError, TypeError, KeyError):
                st.error("The saved learning plan could not be loaded.")

    if not plan:
        st.info("No learning plan is active yet. Go to Home & Profile and generate a plan first.")
    else:
        st.subheader(plan.get("title", "Your Learning Roadmap"))
        st.write(plan.get("overview", "Follow this roadmap consistently and track your progress."))

        st.divider()
        st.subheader("📚 Weekly Learning Roadmap")

        weekly_plan = plan.get("weekly_plan", [])

        if not weekly_plan:
            st.info("No weekly details were returned for this plan.")
        else:
            for week in weekly_plan:
                week_title = week.get("week", "Study Week")
                with st.expander(f"📅 {week_title}", expanded=False):
                    st.markdown("**Topics to learn**")
                    topics = week.get("topics", [])
                    if isinstance(topics, list):
                        for topic_item in topics:
                            st.write(f"• {topic_item}")
                    else:
                        st.write(topics)

                    st.markdown("**Learning activities**")
                    activities = week.get("activities", [])
                    if isinstance(activities, list):
                        for activity in activities:
                            st.write(f"• {activity}")
                    else:
                        st.write(activities)

                    st.markdown("**Weekly milestone**")
                    st.write(week.get("milestone", "Review the topics covered this week."))

        st.divider()
        st.subheader("⏰ Daily Study Routine")

        routine = plan.get("daily_routine", [])
        if routine:
            for item in routine:
                if isinstance(item, dict):
                    activity = item.get("activity", "Study session")
                    minutes = item.get("minutes", 0)
                    st.write(f"• **{activity}** — {minutes} minutes")
                else:
                    st.write(f"• {item}")
        else:
            st.info("No daily routine was provided.")

        st.divider()
        st.subheader("💡 Success Tips")

        tips = plan.get("success_tips", [])
        if tips:
            for tip in tips:
                st.write(f"✅ {tip}")
        else:
            st.write("Study consistently, revise regularly, and practise what you learn.")

        st.download_button(
            label="⬇️ Download Learning Plan (JSON)",
            data=json.dumps(plan, indent=2, ensure_ascii=False),
            file_name="personalized_learning_plan.json",
            mime="application/json",
            use_container_width=True,
        )


if True:
    st.header("🧠 AI-Powered Practice Quiz")
    st.write("Generate a quiz, answer the questions, and review explanations.")

    learner_id = st.session_state.get("learner_id")

    if not learner_id:
        st.warning("Please save your learning profile on the Home & Profile page first.")
    else:
        with st.form("quiz_settings_form"):
            quiz_subject = st.text_input(
                "Subject",
                value=st.session_state.get("learner_subject", "HTML"),
            )
            quiz_topic = st.text_input(
                "Topic",
                value="Web basics and HTML fundamentals",
            )
            quiz_level = st.selectbox(
                "Difficulty",
                ["Beginner", "Intermediate", "Advanced"],
                index=0,
            )
            quiz_count = st.selectbox(
                "Number of questions",
                [5, 10],
                index=0,
            )

            create_quiz = st.form_submit_button(
                "✨ Generate New Quiz",
                use_container_width=True,
            )

        if create_quiz:
            if not quiz_subject.strip() or not quiz_topic.strip():
                st.error("Please enter both a subject and a topic.")
            else:
                with st.spinner("Generating your quiz. Please wait..."):
                    try:
                        quiz = generate_quiz(
                            quiz_subject.strip(),
                            quiz_topic.strip(),
                            quiz_level,
                            num_questions=quiz_count,
                        )
                        st.session_state.active_quiz = quiz
                        st.session_state.quiz_result = None
                        st.session_state.saved_quiz_token = None
                        st.success("Your quiz is ready!")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not generate the quiz: {exc}")

        quiz = st.session_state.get("active_quiz")

        if quiz:
            st.divider()
            st.subheader(quiz.get("title", "Practice Quiz"))
            st.caption(
                f"Subject: {quiz.get('subject', 'N/A')} | "
                f"Topic: {quiz.get('topic', 'N/A')}"
            )

            questions = quiz.get("questions", [])

            if not questions:
                st.warning("This quiz has no questions. Please generate a new quiz.")
            elif st.session_state.get("quiz_result") is None:
                with st.form("quiz_answers_form"):
                    selected_answers = {}

                    for number, question in enumerate(questions, start=1):
                        question_id = str(question.get("id", number))
                        st.markdown(f"**Q{number}. {question.get('question', '')}**")

                        options = question.get("options", {})
                        if isinstance(options, dict):
                            option_letters = list(options.keys())
                            option_labels = [
                                f"{letter}. {options[letter]}"
                                for letter in option_letters
                            ]

                            chosen = st.radio(
                                f"Choose your answer for question {number}",
                                options=option_labels,
                                index=None,
                                key=f"quiz_{id(quiz)}_{question_id}",
                                label_visibility="collapsed",
                            )
                            selected_answers[question_id] = (
                                chosen.split(". ", 1)[0] if chosen else None
                            )
                        else:
                            st.error(f"Question {number} has invalid answer options.")

                        st.write("")

                    submitted = st.form_submit_button(
                        "✅ Submit Answers",
                        use_container_width=True,
                    )

                if submitted:
                    unanswered = [
                        number
                        for number, question in enumerate(questions, start=1)
                        if selected_answers.get(
                            str(question.get("id", number))
                        ) is None
                    ]

                    if unanswered:
                        st.warning(
                            "Please answer every question before submitting. "
                            f"Unanswered question numbers: {', '.join(map(str, unanswered))}"
                        )
                    else:
                        score = 0
                        review = []

                        for number, question in enumerate(questions, start=1):
                            question_id = str(question.get("id", number))
                            chosen_answer = selected_answers.get(question_id)
                            correct_answer = str(question.get("correct_answer", "")).strip()
                            is_correct = chosen_answer == correct_answer

                            if is_correct:
                                score += 1

                            options = question.get("options", {})
                            review.append({
                                "number": number,
                                "question": question.get("question", ""),
                                "chosen": chosen_answer,
                                "chosen_text": options.get(chosen_answer, "No answer")
                                if isinstance(options, dict) else "No answer",
                                "correct": correct_answer,
                                "correct_text": options.get(correct_answer, "Not provided")
                                if isinstance(options, dict) else "Not provided",
                                "is_correct": is_correct,
                                "explanation": question.get(
                                    "explanation",
                                    "Review this concept in your learning materials.",
                                ),
                            })

                        total = len(questions)
                        accuracy = round((score / total) * 100, 1) if total else 0

                        st.session_state.quiz_result = {
                            "score": score,
                            "total": total,
                            "accuracy": accuracy,
                            "review": review,
                            "topic": quiz.get("topic", "Practice Quiz"),
                        }

                        quiz_token = str(id(quiz))
                        if st.session_state.get("saved_quiz_token") != quiz_token:
                            try:
                                save_quiz_attempt(
                                    learner_id,
                                    quiz.get("topic", "Practice Quiz"),
                                    score,
                                    total,
                                    json.dumps({
                                        "answers": selected_answers,
                                        "review": review,
                                    }, ensure_ascii=False),
                                )
                                st.session_state.saved_quiz_token = quiz_token
                            except Exception as exc:
                                st.error(f"Your result could not be saved: {exc}")

                        st.rerun()

            result = st.session_state.get("quiz_result")

            if result:
                st.divider()
                st.subheader("📊 Your Quiz Results")

                col1, col2, col3 = st.columns(3)
                col1.metric("Score", f"{result['score']} / {result['total']}")
                col2.metric("Accuracy", f"{result['accuracy']}%")
                col3.metric(
                    "Questions to review",
                    sum(1 for item in result["review"] if not item["is_correct"]),
                )

                if result["accuracy"] >= 80:
                    st.success("Great work! Keep revising to strengthen your knowledge.")
                elif result["accuracy"] >= 50:
                    st.info("Good effort. Review the explanations and try again.")
                else:
                    st.warning("Keep practising. Review the concepts and take another quiz.")

                st.subheader("📝 Answer Review")

                for item in result["review"]:
                    icon = "✅" if item["is_correct"] else "❌"
                    with st.expander(
                        f"{icon} Question {item['number']}",
                        expanded=not item["is_correct"],
                    ):
                        st.write(item["question"])
                        st.write(f"**Your answer:** {item['chosen']}. {item['chosen_text']}")
                        st.write(f"**Correct answer:** {item['correct']}. {item['correct_text']}")
                        st.write(f"**Explanation:** {item['explanation']}")

                if st.button("🔄 Start Another Quiz", use_container_width=True):
                    st.session_state.active_quiz = None
                    st.session_state.quiz_result = None
                    st.session_state.saved_quiz_token = None
                    st.rerun()

if True:
    st.header("📊 Your Learning Progress Dashboard")

    learner_id = st.session_state.get("learner_id")

    if not learner_id:
        st.warning("Please save your learning profile on the Home & Profile page first.")
    else:
        attempts = get_quiz_attempts(learner_id)
        plans = get_learning_plans(learner_id)

        total_attempts = len(attempts)
        total_questions = sum(int(item.get("total_questions", 0)) for item in attempts)
        total_correct = sum(int(item.get("score", 0)) for item in attempts)

        overall_accuracy = (
            round((total_correct / total_questions) * 100, 1)
            if total_questions else 0
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Quiz Attempts", total_attempts)
        col2.metric("Correct Answers", total_correct)
        col3.metric("Overall Accuracy", f"{overall_accuracy}%")
        col4.metric("Saved Plans", len(plans))

        st.divider()
        st.subheader("📈 Quiz Performance")

        if attempts:
            # Display attempts from oldest to newest for the chart.
            chart_attempts = list(reversed(attempts))
            chart_data = []

            for index, attempt in enumerate(chart_attempts, start=1):
                total = int(attempt.get("total_questions", 0))
                score = int(attempt.get("score", 0))
                accuracy = round((score / total) * 100, 1) if total else 0

                chart_data.append({
                    "Attempt": f"Attempt {index}",
                    "Accuracy (%)": accuracy,
                })

            st.line_chart(
                chart_data,
                x="Attempt",
                y="Accuracy (%)",
            )

            st.divider()
            st.subheader("🧾 Recent Quiz Attempts")

            history_rows = []

            for attempt in attempts:
                total = int(attempt.get("total_questions", 0))
                score = int(attempt.get("score", 0))
                accuracy = round((score / total) * 100, 1) if total else 0

                history_rows.append({
                    "Topic": attempt.get("topic", "Practice Quiz"),
                    "Score": f"{score}/{total}",
                    "Accuracy": f"{accuracy}%",
                    "Date": str(attempt.get("created_at", "")),
                })

            st.dataframe(
                history_rows,
                use_container_width=True,
                hide_index=True,
            )

            history_download = json.dumps(
                history_rows,
                indent=2,
                ensure_ascii=False,
            )

            st.download_button(
                "⬇️ Download Quiz History",
                data=history_download,
                file_name="quiz_history.json",
                mime="application/json",
                use_container_width=True,
            )
        else:
            st.info("No quiz attempts have been saved yet. Take a practice quiz to begin tracking progress.")

        st.divider()
        st.subheader("📚 Your Saved Learning Plans")

        if plans:
            for index, saved_plan in enumerate(plans, start=1):
                with st.expander(
                    f"Learning Plan {index} — {saved_plan.get('created_at', '')}",
                    expanded=False,
                ):
                    try:
                        saved_plan_data = json.loads(saved_plan["plan_json"])
                        st.write(saved_plan_data.get("title", "Personalized Learning Plan"))
                        st.write(saved_plan_data.get("overview", ""))

                        st.download_button(
                            "⬇️ Download This Plan",
                            data=json.dumps(
                                saved_plan_data,
                                indent=2,
                                ensure_ascii=False,
                            ),
                            file_name=f"learning_plan_{index}.json",
                            mime="application/json",
                            key=f"download_plan_{saved_plan.get('id', index)}",
                        )
                    except (json.JSONDecodeError, TypeError, KeyError):
                        st.error("This saved plan could not be read.")
        else:
            st.info("Your saved learning plans will appear here.")

        st.divider()
        st.subheader("🎯 Recommended Next Steps")

        if overall_accuracy >= 80:
            st.write("✅ Keep your momentum. Increase the difficulty or explore a new topic.")
        elif overall_accuracy >= 50:
            st.write("📘 Review incorrect answers and repeat the topics you find challenging.")
        else:
            st.write("🌱 Start with the fundamentals, study in short sessions, and practise regularly.")

        st.write("💡 Tip: Take quizzes regularly so your dashboard can show your improvement over time.")


# Footer
st.divider()
st.caption("AI Personalized Learning Coach | Learn • Practise • Improve")
