import random
from locust import HttpUser, task, between

# Sample data for the load test
PYTHON_SAMPLES = [
    {
        "candidate_id": "student_A",
        "question_id": "LOAD_TEST",
        "language": "python",
        "source_code": "def add(a, b):\n    return a + b",
    },
    {
        "candidate_id": "student_B",
        "question_id": "LOAD_TEST",
        "language": "python",
        "source_code": "def sum_nums(x, y):\n    res = x + y\n    return res",
    },
]

JAVA_SAMPLES = [
    {
        "candidate_id": "java_A",
        "question_id": "LOAD_TEST",
        "language": "java",
        "source_code": "public class Calc { public int add(int a, int b) { return a + b; } }",
    },
    {
        "candidate_id": "java_B",
        "question_id": "LOAD_TEST",
        "language": "java",
        "source_code": "public class Math { public int sum(int x, int y) { int r = x + y; return r; } }",
    },
]


class PlagiarismUser(HttpUser):
    # This tells locust where your server is running automatically
    host = "http://localhost:8000"

    # Wait between 1 and 2 seconds between "submissions"
    wait_time = between(1, 2)

    @task
    def check_plagiarism_python(self):
        # Using the new /check-raw endpoint we added to main.py
        payload = [random.choice(PYTHON_SAMPLES), random.choice(PYTHON_SAMPLES)]
        self.client.post("/check-raw", json=payload)

    @task(2)  # Java is twice as common in this simulation
    def check_plagiarism_java(self):
        # Using the new /check-raw endpoint we added to main.py
        payload = [random.choice(JAVA_SAMPLES), random.choice(JAVA_SAMPLES)]
        self.client.post("/check-raw", json=payload)
