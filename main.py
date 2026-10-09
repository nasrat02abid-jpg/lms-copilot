from playwright.sync_api import sync_playwright
from lms import (
    login,
    get_courses,
    get_assignments,
    get_assignment_details,
    classify_assignment,
    parse_due_date
)


def main():
    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        if not login(page):
            input("Press Enter to close...")
            browser.close()
            return

        courses = get_courses(page)

        all_assignments = []

        print("\n======================================")
        print("             LMS COPILOT")
        print("======================================")

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

                category = classify_assignment(details)

                details["category"] = category

                all_assignments.append(details)

        # Sort by due date
        all_assignments.sort(
            key=lambda x: (
                parse_due_date(x["due_date"])
                is None,
                parse_due_date(x["due_date"])
            )
        )

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

        print("\n🔴 URGENT")
        print("--------------------------------------")

        if not urgent:
            print("No urgent assignments.")

        for item in urgent:
            print(f"\n📚 {item['course']}")
            print(f"📝 {item['title']}")
            print(f"📅 {item['due_date']}")

        print("\n🟠 DUE SOON")
        print("--------------------------------------")

        if not due_soon:
            print("No assignments due soon.")

        for item in due_soon:
            print(f"\n📚 {item['course']}")
            print(f"📝 {item['title']}")
            print(f"📅 {item['due_date']}")

        print("\n🟡 PENDING")
        print("--------------------------------------")

        if not pending:
            print("No pending assignments.")

        for item in pending:
            print(f"\n📚 {item['course']}")
            print(f"📝 {item['title']}")
            print(f"📅 {item['due_date']}")

        print("\n❌ OVERDUE")
        print("--------------------------------------")

        if not overdue:
            print("No overdue assignments.")

        for item in overdue:
            print(f"\n📚 {item['course']}")
            print(f"📝 {item['title']}")
            print(f"📅 {item['due_date']}")

        print("\n✅ SUBMITTED")
        print("--------------------------------------")

        for item in submitted:
            print(f"\n📚 {item['course']}")
            print(f"📝 {item['title']}")

        print("\n======================================")
        print("               SUMMARY")
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

        print("\n======================================")

        input("\nPress Enter to close browser...")

        browser.close()


if __name__ == "__main__":
    main()
    