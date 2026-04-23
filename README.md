# Code Plagiarism Detection Service

A production-ready FastAPI service that detects code plagiarism across 26+ programming languages using Token-based and AST-based analysis.

## Project Structure

```
plagiarism-service/
│
├── 📄 main.py                    # FastAPI REST API server (START HERE)
├── 📄 test_75_students.py        # Python 75-student stress test
├── 📄 test_1000_students_java.py # Java 1,000-student stress test
│
├── 📁 models/                    # API request/response schemas
│   └── schemas.py
│
├── 📁 detection/                 # Core detection engines
│   ├── tokenizer.py              # Token-based detection
│   ├── ast_comparator.py         # AST-based detection
│   └── scorer.py                 # Scoring and classification
│
├── 📁 db/                        # Database connection
│   └── neon.py                   # PostgreSQL (Neon) connection
│
└── 📁 docs/                      # Detailed technical documentation
    ├── FINAL_REFACTOR_REPORT.pdf # Official summary report
    ├── DEMO_PRESENTATION.md      # Presentation guide
    └── 📁 archives/              # Background research & deep-dives

```

## Quick Start

### Run Stress Test (Python)
```bash
python test_75_students.py
```

### Run Stress Test (Java)
```bash
python test_1000_students_java.py
```

### Start API Server
```bash
uvicorn main:app --reload
```

Then visit: http://localhost:8000/docs

## Features

- ✅ 26+ programming languages supported
- ✅ Dual-engine detection (Token + AST)
- ✅ Catches renamed variables and dummy code
- ✅ 7+ architectural fixes for enterprise stability (DFS, k-gram tuning)
- ✅ 7 risk classification levels
- ✅ REST API with automatic documentation
- ✅ Scalable batch processing

## Documentation

See the `docs/` folder for technical reports:
- `DEMO_PRESENTATION.md` - Complete presentation guide
- [FINAL_REFACTOR_REPORT.pdf](docs/FINAL_REFACTOR_REPORT.pdf) - Official summary report

Detailed research and algorithm deep-dives can be found in `docs/archives/`:
- `WINNOWING_STEP_BY_STEP.md` - Algorithm explanation
- `TOKENIZER_EXPLAINED.md` - Tokenizer deep dive
- `ALTERNATIVE_METHODS.md` - Research notes
