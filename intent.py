from datetime import datetime, timedelta


def detect_intent(command):
    command = command.lower().strip()

    result = {
        "intent": "unknown",
        "course": None,
        "filter": None,
        "activity_type": None,
        "time_filter": None
    }

    # ----------------------------
    # COURSE
    # ----------------------------

    if "data science" in command:
        result["course"] = "data science"

    elif "data structure" in command:
        result["course"] = "data structure"

    elif "linear algebra" in command:
        result["course"] = "linear algebra"

    elif "software engineering" in command:
        result["course"] = "software engineering"

    elif (
        "assembly" in command
        or "computer organization" in command
        or "coal" in command
    ):
        result["course"] = "computer organization"

    # ----------------------------
    # ACTIVITY TYPE
    # ----------------------------

    if "quiz" in command or "quizzes" in command:
        result["activity_type"] = "quiz"

    elif "assignment" in command or "assignments" in command:
        result["activity_type"] = "assignment"

    elif (
        "activity" in command
        or "activities" in command
        or "work" in command
        or "task" in command
    ):
        result["activity_type"] = "all"

    # ----------------------------
    # TIME
    # ----------------------------

    if "tomorrow" in command:
        result["time_filter"] = "tomorrow"

    elif "next week" in command:
        result["time_filter"] = "next_week"

    elif "this week" in command:
        result["time_filter"] = "this_week"

    elif "today" in command:
        result["time_filter"] = "today"

    # ----------------------------
    # STATUS
    # ----------------------------

    if "overdue" in command:
        result["filter"] = "overdue"

    elif "urgent" in command:
        result["filter"] = "urgent"

    elif "submitted" in command:
        result["filter"] = "submitted"

    elif "pending" in command:
        result["filter"] = "pending"

    elif "due soon" in command:
        result["filter"] = "due_soon"

    # ----------------------------
    # NEXT ITEM
    # ----------------------------

    if (
        "next deadline" in command
        or "closest deadline" in command
        or "nearest deadline" in command
        or "next assignment" in command
        or "next quiz" in command
        or "what should i do first" in command
    ):
        result["intent"] = "next_activity"

        return result

    # ----------------------------
    # UPCOMING ACTIVITY
    # ----------------------------

    words = [
        "assignment",
        "assignments",
        "quiz",
        "quizzes",
        "activity",
        "activities",
        "work",
        "task",
        "tasks",
        "deadline",
        "due",
        "coming up"
    ]

    if any(word in command for word in words):
        result["intent"] = "check_activities"

    return result