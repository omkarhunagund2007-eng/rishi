import html
import json
import os
import random
from collections import defaultdict
from functools import wraps
from time import time

from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from schema import AttemptAnswer, Question, QuizAttempt, User, db


SUBJECTS = [
    "Quantitative Aptitude",
    "Reasoning",
    "English",
    "General Knowledge",
]


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///govprep.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_database()

    register_routes(app)
    return app


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in first.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access is required for that page.", "error")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)

    return wrapped


def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def seed_database():
    if not User.query.filter_by(username="admin").first():
        db.session.add(
            User(
                username="admin",
                email="admin@govprep.local",
                password_hash=generate_password_hash("admin123"),
                role="admin",
            )
        )

    if Question.query.count() == 0:
        db.session.add_all(Question(**item) for item in seed_questions())

    db.session.commit()


def seed_questions():
    return [
        {
            "subject": "Quantitative Aptitude",
            "difficulty": "Easy",
            "text": "If 20% of a number is 46, what is the number?",
            "option_a": "184",
            "option_b": "210",
            "option_c": "230",
            "option_d": "250",
            "correct_option": "C",
            "explanation": "20% is one fifth, so the number is 46 x 5 = 230.",
        },
        {
            "subject": "Quantitative Aptitude",
            "difficulty": "Medium",
            "text": "A train travels 180 km in 3 hours. What is its average speed?",
            "option_a": "45 km/h",
            "option_b": "55 km/h",
            "option_c": "60 km/h",
            "option_d": "75 km/h",
            "correct_option": "C",
            "explanation": "Average speed = distance / time = 180 / 3 = 60 km/h.",
        },
        {
            "subject": "Quantitative Aptitude",
            "difficulty": "Medium",
            "text": "The ratio of boys to girls is 3:2. If there are 30 boys, how many girls are there?",
            "option_a": "15",
            "option_b": "18",
            "option_c": "20",
            "option_d": "24",
            "correct_option": "C",
            "explanation": "3 parts equal 30, so 1 part is 10. Girls are 2 parts = 20.",
        },
        {
            "subject": "Reasoning",
            "difficulty": "Easy",
            "text": "Find the next number in the series: 2, 4, 8, 16, ?",
            "option_a": "20",
            "option_b": "24",
            "option_c": "30",
            "option_d": "32",
            "correct_option": "D",
            "explanation": "Each term is doubled.",
        },
        {
            "subject": "Reasoning",
            "difficulty": "Medium",
            "text": "If CAT is coded as DBU, how is DOG coded?",
            "option_a": "EPH",
            "option_b": "FQI",
            "option_c": "CNG",
            "option_d": "EQH",
            "correct_option": "A",
            "explanation": "Each letter is shifted one position forward.",
        },
        {
            "subject": "Reasoning",
            "difficulty": "Hard",
            "text": "A is taller than B. C is taller than A. Who is the tallest?",
            "option_a": "A",
            "option_b": "B",
            "option_c": "C",
            "option_d": "Cannot be determined",
            "correct_option": "C",
            "explanation": "C is taller than A, and A is taller than B.",
        },
        {
            "subject": "English",
            "difficulty": "Easy",
            "text": "Choose the correctly spelled word.",
            "option_a": "Accomodate",
            "option_b": "Acommodate",
            "option_c": "Accommodate",
            "option_d": "Acomodate",
            "correct_option": "C",
            "explanation": "The correct spelling is accommodate.",
        },
        {
            "subject": "English",
            "difficulty": "Medium",
            "text": "Choose the synonym of 'brief'.",
            "option_a": "Lengthy",
            "option_b": "Short",
            "option_c": "Complex",
            "option_d": "Late",
            "correct_option": "B",
            "explanation": "Brief means short in duration or length.",
        },
        {
            "subject": "English",
            "difficulty": "Medium",
            "text": "Fill in the blank: She is good ___ mathematics.",
            "option_a": "in",
            "option_b": "at",
            "option_c": "on",
            "option_d": "for",
            "correct_option": "B",
            "explanation": "The correct phrase is 'good at'.",
        },
        {
            "subject": "General Knowledge",
            "difficulty": "Easy",
            "text": "Who is known as the Father of the Indian Constitution?",
            "option_a": "Mahatma Gandhi",
            "option_b": "B. R. Ambedkar",
            "option_c": "Jawaharlal Nehru",
            "option_d": "Sardar Patel",
            "correct_option": "B",
            "explanation": "Dr. B. R. Ambedkar chaired the drafting committee.",
        },
        {
            "subject": "General Knowledge",
            "difficulty": "Easy",
            "text": "Which planet is known as the Red Planet?",
            "option_a": "Venus",
            "option_b": "Mars",
            "option_c": "Jupiter",
            "option_d": "Saturn",
            "correct_option": "B",
            "explanation": "Mars appears reddish because of iron oxide on its surface.",
        },
        {
            "subject": "General Knowledge",
            "difficulty": "Medium",
            "text": "The Reserve Bank of India was established in which year?",
            "option_a": "1935",
            "option_b": "1947",
            "option_c": "1950",
            "option_d": "1969",
            "correct_option": "A",
            "explanation": "The RBI began operations on April 1, 1935.",
        },
    ]


def register_routes(app):
    @app.route("/")
    def index():
        if "user_id" in session:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = User.query.filter_by(username=username).first()

            if user and check_password_hash(user.password_hash, password):
                session.clear()
                session["user_id"] = user.id
                session["username"] = user.username
                session["role"] = user.role
                flash("Signed in successfully.", "success")
                return redirect(url_for("dashboard"))

            flash("Invalid username or password.", "error")

        return render_template("login.html")

    @app.route("/register", methods=["POST"])
    def register():
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "student")

        if role not in {"student", "admin"}:
            role = "student"

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return redirect(url_for("login"))

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email already exists.", "error")
            return redirect(url_for("login"))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created. You can sign in now.", "success")
        return redirect(url_for("login"))

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        user = current_user()
        attempts = (
            QuizAttempt.query.filter_by(user_id=user.id)
            .order_by(QuizAttempt.date_taken.desc())
            .limit(10)
            .all()
        )
        return render_template(
            "dashboard.html",
            active_page="dashboard",
            stats=dashboard_stats(user.id),
            attempts=attempts,
            cache_buster=int(time()),
        )

    @app.route("/quiz")
    @login_required
    def quiz_select():
        return render_template("quiz_select.html", active_page="quiz_select")

    @app.route("/quiz/start", methods=["POST"])
    @login_required
    def quiz_start():
        subject = request.form.get("subject", SUBJECTS[0])
        count = clamp_int(request.form.get("num_questions"), 5, 1, 50)
        duration_minutes = clamp_int(request.form.get("duration"), 5, 1, 180)

        query = Question.query
        if subject != "Full-Length Mock":
            query = query.filter_by(subject=subject)

        questions = query.all()
        if not questions:
            flash("No questions are available for that subject yet.", "error")
            return redirect(url_for("quiz_select"))

        random.shuffle(questions)
        selected = questions[: min(count, len(questions))]
        session["quiz_question_ids"] = [question.id for question in selected]
        session["quiz_subject"] = subject
        session["quiz_duration_seconds"] = duration_minutes * 60

        return render_template(
            "quiz.html",
            active_page="quiz",
            quiz_subject=subject,
            questions=[question.to_quiz_dict() for question in selected],
            duration_seconds=duration_minutes * 60,
        )

    @app.route("/quiz/submit", methods=["POST"])
    @login_required
    def quiz_submit():
        question_ids = session.get("quiz_question_ids", [])
        subject = session.get("quiz_subject", "Mock Test")

        if not question_ids:
            flash("No active quiz was found. Please start a new test.", "error")
            return redirect(url_for("quiz_select"))

        answers = parse_answers(request.form.get("answers_json", "{}"))
        questions = Question.query.filter(Question.id.in_(question_ids)).all()
        questions_by_id = {question.id: question for question in questions}
        ordered_questions = [questions_by_id[qid] for qid in question_ids if qid in questions_by_id]
        correct_count = 0

        attempt = QuizAttempt(
            user_id=session["user_id"],
            subject=subject,
            total_questions=len(ordered_questions),
            correct_answers=0,
            percentage=0,
            time_taken=max(0, int(request.form.get("time_taken") or 0)),
        )
        db.session.add(attempt)
        db.session.flush()

        for question in ordered_questions:
            selected = normalize_option(answers.get(str(question.id)) or answers.get(question.id))
            is_correct = selected == question.correct_option
            correct_count += 1 if is_correct else 0
            db.session.add(
                AttemptAnswer(
                    attempt_id=attempt.id,
                    question_id=question.id,
                    selected_option=selected,
                    correct_option=question.correct_option,
                    is_correct=is_correct,
                )
            )

        attempt.correct_answers = correct_count
        attempt.percentage = round((correct_count / max(1, len(ordered_questions))) * 100, 2)
        db.session.commit()

        session.pop("quiz_question_ids", None)
        session.pop("quiz_subject", None)
        session.pop("quiz_duration_seconds", None)

        flash("Quiz submitted successfully.", "success")
        return redirect(url_for("quiz_result", attempt_id=attempt.id))

    @app.route("/quiz/result/<int:attempt_id>")
    @login_required
    def quiz_result(attempt_id):
        attempt = db.session.get(QuizAttempt, attempt_id)
        if not attempt:
            flash("Attempt not found.", "error")
            return redirect(url_for("dashboard"))

        if attempt.user_id != session["user_id"] and session.get("role") != "admin":
            flash("You cannot view that attempt.", "error")
            return redirect(url_for("dashboard"))

        return render_template(
            "quiz_result.html",
            active_page="quiz",
            attempt=attempt,
            questions_answers=attempt.answers,
        )

    @app.route("/admin")
    @login_required
    @admin_required
    def admin():
        return render_template(
            "admin.html",
            active_page="admin",
            questions=Question.query.order_by(Question.id.desc()).all(),
            users=User.query.order_by(User.created_at.desc()).all(),
            all_attempts=QuizAttempt.query.order_by(QuizAttempt.date_taken.desc()).all(),
        )

    @app.route("/admin/questions/add", methods=["POST"])
    @login_required
    @admin_required
    def admin_add_question():
        question = Question(
            subject=request.form.get("subject", SUBJECTS[0]),
            difficulty=request.form.get("difficulty", "Medium"),
            text=request.form.get("text", "").strip(),
            option_a=request.form.get("option_a", "").strip(),
            option_b=request.form.get("option_b", "").strip(),
            option_c=request.form.get("option_c", "").strip(),
            option_d=request.form.get("option_d", "").strip(),
            correct_option=normalize_option(request.form.get("correct_option")) or "A",
            explanation=request.form.get("explanation", "").strip(),
        )

        if not all([question.text, question.option_a, question.option_b, question.option_c, question.option_d]):
            flash("Please fill in all question fields.", "error")
            return redirect(url_for("admin"))

        db.session.add(question)
        db.session.commit()
        flash("Question added to the bank.", "success")
        return redirect(url_for("admin"))

    @app.route("/admin/questions/<int:question_id>/delete", methods=["POST"])
    @login_required
    @admin_required
    def admin_delete_question(question_id):
        question = db.session.get(Question, question_id)
        if not question:
            flash("Question not found.", "error")
            return redirect(url_for("admin"))

        db.session.delete(question)
        db.session.commit()
        flash("Question deleted.", "success")
        return redirect(url_for("admin"))

    @app.route("/charts/accuracy.svg")
    @login_required
    def accuracy_chart():
        attempts = QuizAttempt.query.filter_by(user_id=session["user_id"]).all()
        subject_scores = defaultdict(list)
        for attempt in attempts:
            if attempt.subject == "Full-Length Mock":
                continue
            subject_scores[attempt.subject].append(attempt.percentage)

        labels = list(subject_scores.keys())
        values = [round(sum(scores) / len(scores), 1) for scores in subject_scores.values()]
        return svg_response(bar_chart_svg(labels, values, "Subject Accuracy"))

    @app.route("/charts/trend.svg")
    @login_required
    def trend_chart():
        attempts = (
            QuizAttempt.query.filter_by(user_id=session["user_id"])
            .order_by(QuizAttempt.date_taken.asc())
            .all()
        )
        labels = [str(index + 1) for index, _attempt in enumerate(attempts)]
        values = [attempt.percentage for attempt in attempts]
        return svg_response(line_chart_svg(labels, values, "Attempt Trend"))


def dashboard_stats(user_id):
    attempts = QuizAttempt.query.filter_by(user_id=user_id).order_by(QuizAttempt.date_taken.asc()).all()
    has_data = bool(attempts)

    if not has_data:
        return {
            "has_data": False,
            "total_attempts": 0,
            "overall_accuracy": 0,
            "strongest_subject": None,
            "strongest_score": 0,
            "weakest_subject": None,
            "weakest_score": 0,
            "weak_areas_tips": [],
            "accuracy_chart_url": url_for("accuracy_chart"),
            "trend_chart_url": url_for("trend_chart"),
        }

    subject_scores = defaultdict(list)
    for attempt in attempts:
        subject_scores[attempt.subject].append(attempt.percentage)

    averages = {
        subject: round(sum(scores) / len(scores), 1)
        for subject, scores in subject_scores.items()
    }
    strongest_subject = max(averages, key=averages.get)
    weakest_subject = min(averages, key=averages.get)
    overall_accuracy = round(sum(attempt.percentage for attempt in attempts) / len(attempts), 1)

    tips = [
        f"Focus your next practice session on {weakest_subject}; your current average is {averages[weakest_subject]}%.",
        "Review every incorrect answer from your latest reports before taking another timed quiz.",
        "Keep alternating subjects so your full-length mock performance stays balanced.",
    ]

    return {
        "has_data": True,
        "total_attempts": len(attempts),
        "overall_accuracy": overall_accuracy,
        "strongest_subject": strongest_subject,
        "strongest_score": averages[strongest_subject],
        "weakest_subject": weakest_subject,
        "weakest_score": averages[weakest_subject],
        "weak_areas_tips": tips,
        "accuracy_chart_url": url_for("accuracy_chart"),
        "trend_chart_url": url_for("trend_chart"),
    }


def clamp_int(value, default, minimum, maximum):
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def parse_answers(raw):
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def normalize_option(value):
    if not value:
        return None
    option = str(value).strip().upper()
    return option if option in {"A", "B", "C", "D"} else None


def svg_response(svg):
    return Response(svg, mimetype="image/svg+xml")


def bar_chart_svg(labels, values, title):
    width, height = 680, 320
    if not labels:
        return empty_chart_svg(title)

    max_value = max(100, max(values))
    chart_left, chart_bottom, chart_top = 60, 260, 50
    slot = (width - chart_left - 30) / len(labels)
    bars = []
    for index, (label, value) in enumerate(zip(labels, values)):
        bar_height = (value / max_value) * (chart_bottom - chart_top)
        x = chart_left + index * slot + slot * 0.2
        y = chart_bottom - bar_height
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{slot * 0.6:.1f}" height="{bar_height:.1f}" rx="4" fill="#4f46e5" />'
            f'<text x="{x + slot * 0.3:.1f}" y="{y - 8:.1f}" text-anchor="middle" font-size="13" fill="#e5e7eb">{value}%</text>'
            f'<text x="{x + slot * 0.3:.1f}" y="292" text-anchor="middle" font-size="12" fill="#9ca3af">{html.escape(label[:16])}</text>'
        )

    return chart_shell(width, height, title, "".join(bars))


def line_chart_svg(labels, values, title):
    width, height = 680, 320
    if not labels:
        return empty_chart_svg(title)

    chart_left, chart_right, chart_bottom, chart_top = 60, 640, 260, 50
    step = (chart_right - chart_left) / max(1, len(values) - 1)
    points = []
    for index, value in enumerate(values):
        x = chart_left + index * step
        y = chart_bottom - (value / 100) * (chart_bottom - chart_top)
        points.append((x, y, value))

    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y, _value in points)
    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#22c55e" />'
        f'<text x="{x:.1f}" y="{y - 12:.1f}" text-anchor="middle" font-size="12" fill="#e5e7eb">{value:.0f}%</text>'
        for x, y, value in points
    )
    body = f'<polyline points="{polyline}" fill="none" stroke="#22c55e" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />{dots}'
    return chart_shell(width, height, title, body)


def empty_chart_svg(title):
    return chart_shell(
        680,
        320,
        title,
        '<text x="340" y="170" text-anchor="middle" font-size="16" fill="#9ca3af">No attempt data yet</text>',
    )


def chart_shell(width, height, title, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" rx="14" fill="#0f172a"/>
<text x="24" y="30" font-size="18" font-family="Arial, sans-serif" font-weight="700" fill="#f8fafc">{html.escape(title)}</text>
<line x1="60" y1="260" x2="640" y2="260" stroke="#334155"/>
<line x1="60" y1="50" x2="60" y2="260" stroke="#334155"/>
{body}
</svg>"""


app = create_app()


if __name__ == "__main__":
    app.run(debug=True,port=3000)
