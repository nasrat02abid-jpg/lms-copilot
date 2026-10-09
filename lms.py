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

    course_links = page.locator('a[href*="/course/view.php"]')

    courses = []
    seen = set()

    for i in range(course_links.count()):
        item = course_links.nth(i)

        name = item.inner_text().strip()
        href = item.get_attribute("href")

        if name and href and name not in seen:
            seen.add(name)

            courses.append({
                "name": name,
                "url": href
            })

    return courses


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
                "url": href
            })

    return assignments


def get_assignment_details(page: Page, assignment, course_name):
    page.goto(assignment["url"])
    page.wait_for_load_state("domcontentloaded")

    details = {
        "course": course_name,
        "title": assignment["title"],
        "due_date": "Not found",
        "status": "Unknown"
    }

    rows = page.locator("tr")

    for i in range(rows.count()):
        text = rows.nth(i).inner_text().strip()

        if not text:
            continue

        lower_text = text.lower()

        if "due date" in lower_text:
            parts = text.split("\t")

            if len(parts) >= 2:
                details["due_date"] = parts[-1].strip()
            else:
                details["due_date"] = text

        if "submission status" in lower_text:
            parts = text.split("\t")

            if len(parts) >= 2:
                details["status"] = parts[-1].strip()
            else:
                details["status"] = text

    return details


def parse_due_date(date_text):
    if not date_text or date_text == "Not found":
        return None

    formats = [
        "%A, %d %B %Y, %I:%M %p",
        "%A, %d %B %Y, %H:%M",
        "%d %B %Y, %I:%M %p",
        "%d %B %Y, %H:%M",
    ]

    cleaned = re.sub(r"\s+", " ", date_text).strip()

    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            pass

    return None


def classify_assignment(details):
    status_text = details["status"].lower()

    if (
        "submitted" in status_text
        or "submitted for grading" in status_text
    ):
        return "submitted"

    due = parse_due_date(details["due_date"])

    if due is None:
        return "pending"

    now = datetime.now()
    difference = due - now
    hours_left = difference.total_seconds() / 3600

    if hours_left < 0:
        return "overdue"

    if hours_left <= 24:
        return "urgent"

    if hours_left <= 72:
        return "due_soon"
    return "pending"