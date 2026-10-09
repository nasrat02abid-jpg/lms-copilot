from playwright.sync_api import sync_playwright

from intent import detect_intent

from lms import (
    login,
    get_courses,
    get_assignments,
    get_assignment_details,
    classify_assignment,
    parse_due_date
)


def show_assignment(item):
    print("\n--------------------------------------")
    print(f"📚 Course: {item['course']}")
    print(f"📝 Assignment: {item['title']}")
    print(f"📅 Due: {item['due_date']}")
    print(f"📌 Status: {item['status']}")
    print(f"⚡ Category: {item['category']}")


def collect_all_assignments(page):
    courses = get_courses(page)

    all_assignments = []

    print("\n🔍 Checking LMS courses and assignments...")

    for course in courses:

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

            all_assignments.append(details)

    # Sort assignments by due date
    all_assignments.sort(
        key=lambda x: (
            parse_due_date(x["due_date"]) is None,
            parse_due_date(x["due_date"])
        )
    )

    return all_assignments


def show_summary(all_assignments):

    urgent = []
    due_soon = []
    pending = []
    overdue = []
    submitted = []

    for item in all_assignments:

        category = item["category"]

        if category == "urgent":
            urgent.append(item)

        elif category == "due_soon":
            due_soon.append(item)

        elif category == "overdue":
            overdue.append(item)

        elif category == "submitted":
            submitted.append(item)

        else:
            pending.append(item)

    print("\n======================================")
    print("             LMS COPILOT")
    print("======================================")

    print(f"🔴 Urgent: {len(urgent)}")
    print(f"🟠 Due Soon: {len(due_soon)}")
    print(f"🟡 Pending: {len(pending)}")
    print(f"❌ Overdue: {len(overdue)}")
    print(f"✅ Submitted: {len(submitted)}")

    actionable = urgent + due_soon + pending

    actionable_with_dates = [
        x for x in actionable
        if parse_due_date(x["due_date"]) is not None
    ]

    if actionable_with_dates:

        nearest = min(
            actionable_with_dates,
            key=lambda x: parse_due_date(
                x["due_date"]
            )
        )

        print("\n🎯 NEXT DEADLINE")
        print("--------------------------------------")
        print(f"Course: {nearest['course']}")
        print(f"Assignment: {nearest['title']}")
        print(f"Due: {nearest['due_date']}")

    print("======================================")


def handle_next_deadline(assignments):

    active = [
        x for x in assignments
        if x["category"] != "submitted"
        and parse_due_date(x["due_date"]) is not None
    ]

    if not active:
        print("\n✅ No upcoming deadline found.")
        return

    nearest = min(
        active,
        key=lambda x: parse_due_date(
            x["due_date"]
        )
    )

    print("\n🎯 YOUR NEXT DEADLINE")

    show_assignment(nearest)


def handle_assignment_search(assignments, intent_data):

    results = assignments.copy()

    course = intent_data["course"]
    assignment_filter = intent_data["filter"]

    # Filter by course
    if course:

        results = [
            x for x in results
            if course in x["course"].lower()
        ]

    # Filter by assignment category
    if assignment_filter:

        if assignment_filter == "pending":

            results = [
                x for x in results
                if x["category"] in [
                    "pending",
                    "due_soon",
                    "urgent"
                ]
            ]

        else:

            results = [
                x for x in results
                if x["category"] == assignment_filter
            ]

    if not results:
        print("\n❌ No matching assignments found.")
        return

    print(
        f"\n✅ Found {len(results)} matching assignment(s)."
    )

    for item in results:
        show_assignment(item)


def command_loop(assignments):

    print("\n🤖 LMS Copilot is ready.")

    print("""
Try commands like:

• show my assignments
• show pending assignments
• show urgent assignments
• show overdue work
• show submitted assignments
• show data science assignments
• show software engineering work
• show urgent data structure assignments
• what is my next deadline
• closest deadline
• summary
• help
• exit
""")

    while True:

        command = input(
            "\n🧑 You: "
        ).strip()

        if not command:
            continue

        command_lower = command.lower()

        # Exit
        if command_lower in [
            "exit",
            "quit",
            "close"
        ]:
            print("\n👋 LMS Copilot closed.")
            break

        # Help
        if command_lower in [
            "help",
            "commands"
        ]:

            print("""
Available examples:

show my assignments
show pending assignments
show urgent assignments
show overdue assignments
show submitted assignments

show data science assignments
show data structure work
show linear algebra assignments
show software engineering work
show assembly assignments

what is my next deadline
closest deadline

summary
exit
""")

            continue

        # Summary
        if command_lower in [
            "summary",
            "show summary"
        ]:

            show_summary(assignments)

            continue

        # Detect natural-language intent
        intent_data = detect_intent(command)

        if intent_data["intent"] == "next_deadline":

            handle_next_deadline(
                assignments
            )

        elif intent_data["intent"] == "check_assignments":

            handle_assignment_search(
                assignments,
                intent_data
            )

        else:

            print(
                "\n🤔 I don't understand that command yet."
            )

            print(
                "Type 'help' to see examples."
            )


def main():

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        if not login(page):

            print("❌ Could not login to LMS.")

            input(
                "\nPress Enter to close..."
            )

            browser.close()

            return

        print("\n✅ LMS login successful.")

        all_assignments = collect_all_assignments(
            page
        )

        print(
            f"\n✅ Found {len(all_assignments)} assignments."
        )

        # Show dashboard summary
        show_summary(
            all_assignments
        )

        # Start natural-language command system
        command_loop(
            all_assignments
        )

        browser.close()


if __name__ == "__main__":
    main()