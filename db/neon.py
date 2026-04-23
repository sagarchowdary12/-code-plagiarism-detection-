# The Setup: Tools to connect to PostgreSQL
import psycopg2
import os
from dotenv import load_dotenv

# Looks at the hidden '.env' file and loads the secret Neon database password securely into memory.
load_dotenv()


# Getting the Engine Started
def get_connection():
    # Grabs the secret password loaded earlier
    database_url = os.getenv("DATABASE_URL")
    # Reaches across the internet to the Neon Server to open a live pipe
    connection = psycopg2.connect(database_url)
    return connection


# Running the Database Query
def fetch_submissions(batch_id: str):
    connection = get_connection()  # Opens the pipe
    cursor = connection.cursor()  # The 'cursor' executes the SQL commands

    # This SQL literally says: "Give me the candidate's name, the question, their code,
    # and their programming language, but ONLY if they belong to this batch_id."
    query = """
        SELECT
            asc2.candidate_id,
            asc2.question_id,
            asc2.source_code,
            asc2.language
        FROM assessment_submissions_coding asc2
        WHERE asc2.assessment_id = %s
        ORDER BY asc2.question_id, asc2.candidate_id
    """

    cursor.execute(
        query, (batch_id,)
    )  # Runs the query securely with the provided batch_id
    rows = cursor.fetchall()  # Downloads all the database rows

    cursor.close()
    connection.close()

    # Packaging it for Python
    submissions = []  # Creates an empty list
    for row in rows:  # Loops over every student's answer
        # Packages the raw database text into a clean Python Dictionary
        submissions.append(
            {
                "candidate_id": row[0],
                "question_id": row[1],
                "source_code": row[2],
                "language": row[3],
            }
        )

    # Sends the clean list back to main.py
    return submissions
