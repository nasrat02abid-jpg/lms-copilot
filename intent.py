def detect_intent(command):
    
    command = command.lower().strip()

    result = {
        "intent": "unknown",
        "course": None,
        "filter": None
    }

    # ----------------------------
    # COURSE DETECTION
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
        result["course"] = "assembly"

    # ----------------------------
    # FILTER DETECTION
    # ----------------------------

    if "overdue" in command:
        result["filter"] = "overdue"

    elif "urgent" in command:
        result["filter"] = "urgent"

    elif "submitted" in command:
        result["filter"] = "submitted"

    elif "pending" in command:
        result["filter"] = "pending"

    elif (
        "due soon" in command
        or "soon" in command
    ):
        result["filter"] = "due_soon"

    # ----------------------------
    # INTENT DETECTION
    # ----------------------------

    deadline_phrases = [
        "next deadline",
        "closest deadline",
        "nearest deadline",
        "next due",
        "what should i do first"
    ]

    for phrase in deadline_phrases:

        if phrase in command:
            result["intent"] = "next_deadline"
            return result

    assignment_words = [
        "assignment",
        "assignments",
        "work",
        "task",
        "tasks",
        "due",
        "deadline"
    ]

    for word in assignment_words:

        if word in command:
            result["intent"] = "check_assignments"
            return result

    return result