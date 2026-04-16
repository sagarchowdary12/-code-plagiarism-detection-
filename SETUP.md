# Setup Guide

## Prerequisites

- Python 3.8+
- PostgreSQL database (we use Neon serverless)
- Git

## Installation Steps

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd plagiarism-service
```

### 2. Create virtual environment
```bash
python -m venv venv
```

### 3. Activate virtual environment

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

If you prefer to install manually:
```bash
pip install fastapi uvicorn psycopg2-binary python-dotenv pydantic tree-sitter
# Then install individual language parsers...
```

### 5. Create .env file

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://username:password@host:port/database
```

**IMPORTANT:** Never commit the `.env` file to Git! It's already in `.gitignore`.

### 6. Setup database

Make sure your PostgreSQL database has a table for submissions:

```sql
CREATE TABLE submissions (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(255),
    candidate_id VARCHAR(255),
    question_id VARCHAR(255),
    language VARCHAR(50),
    source_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Running the Application

### Run Demo
```bash
python demo_for_team_leader.py
```

### Run Tests
```bash
# Complex evasion test cases
python test_complex_evasion.py
```

### Start API Server
```bash
uvicorn main:app --reload
```

Then visit: http://localhost:8000/docs

## Project Structure

```
plagiarism-service/
├── main.py                    # FastAPI REST API server
├── demo_for_team_leader.py    # Main demonstration script
├── test_complex_evasion.py    # Evasion scenario tests
├── requirements.txt           # Project dependencies
├── db/
│   └── neon.py               # Database connection
├── detection/
│   ├── tokenizer.py          # Token-based detection
│   ├── ast_comparator.py     # AST-based detection
│   └── scorer.py             # Scoring and classification
├── models/
│   └── schemas.py            # API request/response schemas
└── docs/                     # Detailed technical documentation
```

## Troubleshooting

### Tree-sitter installation issues
If you get errors installing tree-sitter parsers, try:
```bash
pip install --upgrade pip
pip install tree-sitter --force-reinstall
```

### Database connection issues
- Check your `.env` file has the correct DATABASE_URL
- Verify your database is running
- Test connection: `psql <your-database-url>`

### Import errors
Make sure you're in the project root directory and virtual environment is activated.

## Support

For issues or questions, contact the development team.
