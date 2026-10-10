from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta

from intent import detect_intent
from voice import listen, speak

from lms import (
    login,
    get_courses,
    get_assignments,
    get_assignment_details,
    get_quizzes,
    get_quiz_details,
    classify_assignment,
    classify_quiz,
    parse_due_date
)


# ==========================================================
# DISPLAY HELPERS
# ==========================================================

def show_activity(item):
    print("\n--------------------------------------")
    print(f"📚 Course: {item['course']}")
    print(f"📌 Type: {item['type'].title()}")
    print(f"📝 Title: {item['title']}")
    print(f"📅 Due: {item['due_date']}")
    print(f"📍 Status: {item['status']}")
    print(f"⚡ Category: {item['category']}")


def activity_to_speech(item):
    activity_type = item["type"]

    return (
        f"{item['title']}, "
        f"a {activity_type} for {item['course']}. "
        f"It is due {item['due_date']}."
    )


# ==========================================================
# COLLECT LMS DATA
# ==========================================================

def collect_all_activities(page):
    courses = get_courses(page)

    all_activities = []

    print("\n🔍 Checking LMS courses...")

    for course in courses:

        print(f"\n📘 Checking {course['name']}")

        # ------------------------------
        # Assignments
        # ------------------------------

        assignments = get_assignments(
            page,
            course
        )

        for assignment in assignments:

            details = get_assignment_details(
                page,
                assignment,
                course["name"]
            )

            details["category"] = classify_assignment(
                details
            )

            all_activities.append(details)

        # ------------------------------
        # Quizzes
        # ------------------------------

        quizzes = get_quizzes(
            page,
            course
        )

        for quiz in quizzes:

            details = get_quiz_details(
                page,
                quiz,
                course["name"]
            )

            details["category"] = classify_quiz(
                details
            )

            all_activities.append(details)

    # Sort by due date
    all_activities.sort(
        key=lambda x: (
            parse_due_date(x["due_date"]) is None,
            parse_due_date(x["due_date"])
            or datetime.max
        )
    )

    return all_activities


# ==========================================================
# DATE FILTERS
# ==========================================================

def is_today(date_value):
    if date_value is None:
        return False

    today = datetime.now().date()

    return date_value.date() == today


def is_tomorrow(date_value):
    if date_value is None:
        return False

    tomorrow = (
        datetime.now().date()
        + timedelta(days=1)
    )

    return date_value.date() == tomorrow


def is_this_week(date_value):
    if date_value is None:
        return False

    today = datetime.now().date()

    start = today

    end = today + timedelta(
        days=(6 - today.weekday())
    )

    return start <= date_value.date() <= end


def is_next_week(date_value):
    if date_value is None:
        return False

    today = datetime.now().date()

    days_until_next_monday = (
        7 - today.weekday()
    )

    next_monday = (
        today
        + timedelta(
            days=days_until_next_monday
        )
    )

    next_sunday = (
        next_monday
        + timedelta(days=6)
    )

    return (
        next_monday
        <= date_value.date()
        <= next_sunday
    )


def filter_by_time(
    activities,
    time_filter
):
    if not time_filter:
        return activities

    results = []

    for item in activities:

        due = parse_due_date(
            item["due_date"]
        )

        if not due:
            continue

        if (
            time_filter == "today"
            and is_today(due)
        ):
            results.append(item)

        elif (
            time_filter == "tomorrow"
            and is_tomorrow(due)
        ):
            results.append(item)

        elif (
            time_filter == "this_week"
            and is_this_week(due)
        ):
            results.append(item)

        elif (
            time_filter == "next_week"
            and is_next_week(due)
        ):
            results.append(item)

    return results


# ==========================================================
# SUMMARY
# ==========================================================

def get_summary_data(activities):
    summary = {
        "urgent": [],
        "due_soon": [],
        "pending": [],
        "overdue": [],
        "submitted": []
    }

    for item in activities:

        category = item["category"]

        if category in summary:
            summary[category].append(item)

        else:
            summary["pending"].append(item)

    return summary


def show_summary(
    activities,
    voice=False
):
    summary = get_summary_data(
        activities
    )

    assignments = [
        x for x in activities
        if x["type"] == "assignment"
    ]

    quizzes = [
        x for x in activities
        if x["type"] == "quiz"
    ]

    print("\n======================================")
    print("             LMS COPILOT")
    print("======================================")

    print(
        f"📝 Assignments: {len(assignments)}"
    )

    print(
        f"🧠 Quizzes: {len(quizzes)}"
    )

    print(
        f"🔴 Urgent: {len(summary['urgent'])}"
    )

    print(
        f"🟠 Due Soon: {len(summary['due_soon'])}"
    )

    print(
        f"🟡 Pending: {len(summary['pending'])}"
    )

    print(
        f"❌ Overdue: {len(summary['overdue'])}"
    )

    print(
        f"✅ Submitted: {len(summary['submitted'])}"
    )

    active = [
        x for x in activities
        if x["category"] != "submitted"
        and parse_due_date(
            x["due_date"]
        ) is not None
    ]

    nearest = None

    if active:

        nearest = min(
            active,
            key=lambda x: parse_due_date(
                x["due_date"]
            )
        )

        print("\n🎯 NEXT ACTIVITY")
        print("--------------------------------------")

        print(
            f"Type: {nearest['type'].title()}"
        )

        print(
            f"Course: {nearest['course']}"
        )

        print(
            f"Title: {nearest['title']}"
        )

        print(
            f"Due: {nearest['due_date']}"
        )

    print("======================================")

    if voice:

        message = (
            f"You have {len(assignments)} assignments "
            f"and {len(quizzes)} quizzes. "
            f"{len(summary['urgent'])} are urgent, "
            f"{len(summary['due_soon'])} are due soon, "
            f"and {len(summary['overdue'])} are overdue."
        )

        if nearest:

            message += (
                f" Your next activity is "
                f"{nearest['title']} "
                f"for {nearest['course']}."
            )

        speak(message)


# ==========================================================
# NEXT ACTIVITY
# ==========================================================

def handle_next_activity(
    activities,
    intent_data,
    voice=False
):
    results = [
        x for x in activities
        if x["category"] != "submitted"
        and parse_due_date(
            x["due_date"]
        ) is not None
    ]

    activity_type = intent_data.get(
        "activity_type"
    )

    course = intent_data.get(
        "course"
    )

    if (
        activity_type
        and activity_type != "all"
    ):

        results = [
            x for x in results
            if x["type"] == activity_type
        ]

    if course:

        results = [
            x for x in results
            if course
            in x["course"].lower()
        ]

    if not results:

        message = (
            "I could not find any upcoming activity."
        )

        print(f"\n✅ {message}")

        if voice:
            speak(message)

        return

    nearest = min(
        results,
        key=lambda x: parse_due_date(
            x["due_date"]
        )
    )

    print("\n🎯 NEXT ACTIVITY")

    show_activity(nearest)

    if voice:
        speak(
            "Your next activity is "
            + activity_to_speech(
                nearest
            )
        )


# ==========================================================
# ACTIVITY SEARCH
# ==========================================================

def handle_activity_search(
    activities,
    intent_data,
    voice=False
):
    results = activities.copy()

    course = intent_data.get(
        "course"
    )

    activity_type = intent_data.get(
        "activity_type"
    )

    category_filter = intent_data.get(
        "filter"
    )

    time_filter = intent_data.get(
        "time_filter"
    )

    # ------------------------------
    # Course
    # ------------------------------

    if course:

        results = [
            x for x in results
            if course
            in x["course"].lower()
        ]

    # ------------------------------
    # Activity type
    # ------------------------------

    if (
        activity_type
        and activity_type != "all"
    ):

        results = [
            x for x in results
            if x["type"] == activity_type
        ]

    # ------------------------------
    # Status
    # ------------------------------

    if category_filter:

        if category_filter == "pending":

            results = [
                x for x in results
                if x["category"]
                in [
                    "pending",
                    "due_soon",
                    "urgent"
                ]
            ]

        else:

            results = [
                x for x in results
                if x["category"]
                == category_filter
            ]

    # ------------------------------
    # Time
    # ------------------------------

    results = filter_by_time(
        results,
        time_filter
    )

    if not results:

        message = (
            "I found no matching activities."
        )

        print(f"\n❌ {message}")

        if voice:
            speak(message)

        return

    print(
        f"\n✅ Found {len(results)} matching activity or activities."
    )

    for item in results:
        show_activity(item)

    if voice:

        if len(results) == 1:

            speak(
                "I found one activity. "
                + activity_to_speech(
                    results[0]
                )
            )

        else:

            speak(
                f"I found {len(results)} activities."
            )

            # Speak first 5 only
            for item in results[:5]:

                speak(
                    activity_to_speech(
                        item
                    )
                )

            if len(results) > 5:

                speak(
                    f"There are "
                    f"{len(results) - 5} "
                    f"more activities shown "
                    f"on the screen."
                )


# ==========================================================
# COMMAND PROCESSOR
# ==========================================================

def process_command(
    command,
    activities,
    voice=False
):
    if not command:
        return True

    command_lower = (
        command.lower().strip()
    )

    # Exit
    if command_lower in [
        "exit",
        "quit",
        "close",
        "stop"
    ]:

        if voice:
            speak(
                "LMS Copilot closed."
            )

        else:
            print(
                "\n👋 LMS Copilot closed."
            )

        return False

    # Help
    if command_lower in [
        "help",
        "commands"
    ]:

        print("""
Try questions like:

show my assignments

show my quizzes

do I have any quiz tomorrow

do I have any quiz next week

what do I have this week

show data science quizzes

show software engineering assignments

what is my next assignment

what is my next quiz

what is my next deadline

show overdue work

show pending activities

summary

exit
""")

        if voice:

            speak(
                "You can ask about assignments, "
                "quizzes, upcoming activities, "
                "today, tomorrow, this week, "
                "next week, or your next deadline."
            )

        return True

    # Summary
    if command_lower in [
        "summary",
        "show summary"
    ]:

        show_summary(
            activities,
            voice=voice
        )

        return True

    intent_data = detect_intent(
        command
    )

    intent = intent_data[
        "intent"
    ]

    if intent in [
        "next_activity",
        "next_deadline"
    ]:

        handle_next_activity(
            activities,
            intent_data,
            voice=voice
        )

    elif intent in [
        "check_activities",
        "check_assignments"
    ]:

        handle_activity_search(
            activities,
            intent_data,
            voice=voice
        )

    else:

        message = (
            "I do not understand that command yet."
        )

        print(
            f"\n🤔 {message}"
        )

        if voice:
            speak(message)

    return True


# ==========================================================
# TEXT MODE
# ==========================================================

def text_command_loop(
    activities
):
    print(
        "\n⌨️ Text mode enabled."
    )

    print(
        "Type help to see commands."
    )

    while True:

        command = input(
            "\n🧑 You: "
        ).strip()

        keep_running = process_command(
            command,
            activities,
            voice=False
        )

        if not keep_running:
            break


# ==========================================================
# VOICE MODE
# ==========================================================

def voice_command_loop(
    activities
):
    print(
        "\n🎤 Voice mode enabled."
    )

    speak(
        "LMS Copilot is ready. "
        "Ask me about your assignments, "
        "quizzes, or upcoming activities."
    )

    while True:

        command = listen()

        if not command:
            continue

        keep_running = process_command(
            command,
            activities,
            voice=True
        )

        if not keep_running:
            break


# ==========================================================
# MODE SELECTION
# ==========================================================

def choose_mode():
    print("\n======================================")
    print("          CHOOSE INPUT MODE")
    print("======================================")

    print("1. Text")
    print("2. Voice")

    while True:

        choice = input(
            "\nChoose 1 or 2: "
        ).strip()

        if choice == "1":
            return "text"

        if choice == "2":
            return "voice"

        print(
            "❌ Please enter 1 or 2."
        )


# ==========================================================
# MAIN
# ==========================================================

def main():
    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        if not login(page):

            print(
                "❌ Could not login to LMS."
            )

            input(
                "\nPress Enter to close..."
            )

            browser.close()

            return

        print(
            "\n✅ LMS login successful."
        )

        all_activities = collect_all_activities(
            page
        )

        assignment_count = len(
            [
                x for x in all_activities
                if x["type"]
                == "assignment"
            ]
        )

        quiz_count = len(
            [
                x for x in all_activities
                if x["type"]
                == "quiz"
            ]
        )

        print(
            f"\n✅ Found {assignment_count} assignments."
        )

        print(
            f"✅ Found {quiz_count} quizzes."
        )

        show_summary(
            all_activities
        )

        mode = choose_mode()

        if mode == "voice":

            voice_command_loop(
                all_activities
            )

        else:

            text_command_loop(
                all_activities
            )

        browser.close()


if __name__ == "__main__":
    main()