from playwright.sync_api import Page
from config import LMS_URL, LMS_USERNAME, LMS_PASSWORD
from datetime import datetime
import re


def login(page: Page):
    print("Opening LMS login page...")

    page.goto(f"{LMS_URL}/login/index.php")
    page.wait_for_load_state("domcontentloaded")

    page.locator("#username").fill(LMS_USERNAME)
    page.locator("#password").fill(LMS_PASSWORD)
    page.locator("#loginbtn").click()

    page.wait_for_load_state("networkidle")

    if "login" in page.url.lower():
        print("❌ Login may have failed.")
        return False

    print("✅ Login successful.")
    return True


def get_courses(page: Page):
    page.goto(f"{LMS_URL}/my/")
    page.wait_for_load_state("networkidle")

    course_links = page.locator(
        'a[href*="/course/view.php"]'
    )

    courses = []
    seen = set()

    for i in range(course_links.count()):
        item = course_links.nth(i)

        name = item.inner_text().strip()
        href = item.get_attribute("href")

        if name and href and href not in seen:
            seen.add(href)

            courses.append({
                "name": name,
                "url": href
            })

    return courses


# ==========================================================
# ASSIGNMENTS
# ==========================================================

def get_assignments(page: Page, course):
    page.goto(course["url"])
    page.wait_for_load_state("networkidle")

    assignment_links = page.locator(
        'a[href*="/mod/assign/view.php"]'
    )

    assignments = []
    seen_urls = set()

    for i in range(assignment_links.count()):
        item = assignment_links.nth(i)

        title = item.inner_text().strip()
        href = item.get_attribute("href")

        if title and href and href not in seen_urls:
            seen_urls.add(href)

            assignments.append({
                "title": title,
                "url": href,
                "type": "assignment"
            })

    return assignments


def get_assignment_details(
    page: Page,
    assignment,
    course_name
):
    page.goto(assignment["url"])
    page.wait_for_load_state("domcontentloaded")

    details = {
        "course": course_name,
        "title": assignment["title"],
        "type": "assignment",
        "due_date": "Not found",
        "status": "Unknown",
        "url": assignment["url"]
    }

    rows = page.locator("tr")

    for i in range(rows.count()):
        text = rows.nth(i).inner_text().strip()

        if not text:
            continue

        lower_text = text.lower()

        if "due date" in lower_text:
            details["due_date"] = extract_row_value(
                text
            )

        if "submission status" in lower_text:
            details["status"] = extract_row_value(
                text
            )

    return details


# ==========================================================
# QUIZZES
# ==========================================================

def get_quizzes(page: Page, course):
    page.goto(course["url"])
    page.wait_for_load_state("networkidle")

    quiz_links = page.locator(
        'a[href*="/mod/quiz/view.php"]'
    )

    quizzes = []
    seen_urls = set()

    for i in range(quiz_links.count()):
        item = quiz_links.nth(i)

        title = item.inner_text().strip()
        href = item.get_attribute("href")

        if title and href and href not in seen_urls:
            seen_urls.add(href)

            quizzes.append({
                "title": title,
                "url": href,
                "type": "quiz"
            })

    return quizzes


def get_quiz_details(
    page: Page,
    quiz,
    course_name
):
    page.goto(quiz["url"])
    page.wait_for_load_state("domcontentloaded")

    details = {
        "course": course_name,
        "title": quiz["title"],
        "type": "quiz",
        "due_date": "Not found",
        "status": "Unknown",
        "url": quiz["url"]
    }

    # Moodle quiz pages often contain text like:
    # "This quiz will close on ..."
    # "Time limit ..."
    # "Attempts allowed ..."

    body_text = page.locator("body").inner_text()

    lines = [
        line.strip()
        for line in body_text.splitlines()
        if line.strip()
    ]

    for line in lines:
        lower_line = line.lower()

        if (
            "quiz will close" in lower_line
            or "closes" in lower_line
            or "close on" in lower_line
        ):
            possible_date = extract_date_from_text(
                line
            )

            if possible_date:
                details["due_date"] = possible_date

        if (
            "attempt" in lower_line
            and "submitted" in lower_line
        ):
            details["status"] = line

        elif "no attempts" in lower_line:
            details["status"] = "Not attempted"

    # Also inspect tables in case this Moodle theme
    # presents quiz dates in rows.
    rows = page.locator("tr")

    for i in range(rows.count()):
        text = rows.nth(i).inner_text().strip()

        if not text:
            continue

        lower_text = text.lower()

        if (
            "close" in lower_text
            or "due date" in lower_text
        ):
            value = extract_row_value(text)

            if parse_due_date(value):
                details["due_date"] = value

    return details


# ==========================================================
# HELPERS
# ==========================================================

def extract_row_value(text):
    parts = text.split("\t")

    if len(parts) >= 2:
        return parts[-1].strip()

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if len(lines) >= 2:
        return lines[-1]

    return text.strip()


def extract_date_from_text(text):
    cleaned = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    patterns = [
        r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), "
        r"\d{1,2} [A-Za-z]+ \d{4}, \d{1,2}:\d{2} [APMapm]{2}",

        r"\d{1,2} [A-Za-z]+ \d{4}, "
        r"\d{1,2}:\d{2} [APMapm]{2}"
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            cleaned
        )

        if match:
            return match.group(0)

    return None


def parse_due_date(date_text):
    if (
        not date_text
        or date_text == "Not found"
    ):
        return None

    cleaned = re.sub(
        r"\s+",
        " ",
        date_text
    ).strip()

    formats = [
        "%A, %d %B %Y, %I:%M %p",
        "%A, %d %B %Y, %H:%M",
        "%d %B %Y, %I:%M %p",
        "%d %B %Y, %H:%M",
        "%A, %d %B %Y",
        "%d %B %Y"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(
                cleaned,
                fmt
            )
        except ValueError:
            pass

    return None


# ==========================================================
# CLASSIFICATION
# ==========================================================

def classify_assignment(details):
    status_text = details[
        "status"
    ].lower()

    if (
        "submitted" in status_text
        or "submitted for grading"
        in status_text
    ):
        return "submitted"

    return classify_by_date(
        details["due_date"]
    )


def classify_quiz(details):
    status_text = details[
        "status"
    ].lower()

    if (
        "submitted" in status_text
        or "finished" in status_text
        or "completed" in status_text
    ):
        return "submitted"

    return classify_by_date(
        details["due_date"]
    )


def classify_by_date(date_text):
    due = parse_due_date(
        date_text
    )

    if due is None:
        return "pending"

    now = datetime.now()

    difference = due - now

    hours_left = (
        difference.total_seconds()
        / 3600
    )

    if hours_left < 0:
        return "overdue"

    if hours_left <= 24:
        return "urgent"

    if hours_left <= 72:
        return "due_soon"

    return "pending"