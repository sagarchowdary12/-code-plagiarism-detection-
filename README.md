# Code Plagiarism Detection Service

A production-ready FastAPI service that detects code plagiarism across 26+ programming languages using Token-based and AST-based analysis.

## Project Structure

```
plagiarism-service/
│
├── 📄 main.py                    # FastAPI REST API server (START HERE)
├── 📄 demo_for_team_leader.py    # Main demonstration script
├── 📄 test_complex_evasion.py    # Evasion scenario tests
├── 📄 test_fixes.py             # Feature verification tests
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
    ├── DEMO_PRESENTATION.md      # Complete presentation guide
    ├── WINNOWING_STEP_BY_STEP.md # Algorithm explanation
    └── ...

```

## Quick Start

### Run Demo
```bash
python demo_for_team_leader.py
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
- ✅ Tree-Sitter Winnowing prevents AST destruction
- ✅ 7 risk classification levels
- ✅ REST API with automatic documentation
- ✅ Scalable batch processing

## Documentation

See the `docs/` folder for detailed documentation:
- `DEMO_PRESENTATION.md` - Complete presentation guide
- `WINNOWING_STEP_BY_STEP.md` - Algorithm explanation
- `TOKENIZER_EXPLAINED.md` - Tokenizer deep dive
- And more...
