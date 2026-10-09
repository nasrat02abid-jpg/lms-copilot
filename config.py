import os
from dotenv import load_dotenv

load_dotenv()

LMS_URL = os.getenv("LMS_URL")
LMS_USERNAME = os.getenv("LMS_USERNAME")
LMS_PASSWORD = os.getenv("LMS_PASSWORD")

COURSES = [
    "Data Structure",
    "Computer Organization and Assembly Language",
    "Introduction to Data Science",
    "Linear Algebra",
    "Software Engineering",
]