# Quick Start: Critic Agent Evaluation System

## 🚀 Installation

First, install the new dependency:

```bash
pip install sqlalchemy>=2.0.0
# OR
pip install -r requirements.txt  # (sqlalchemy already added)
```

## ▶️ Running the System

### 1. Run Full Pipeline (includes evaluation)

```bash
python main.py
```

This will now run 4 phases:
- Phase 1: Data Collection
- Phase 2: Data Cleaning
- Phase 3: Data Labeling
- Phase 4: Data Evaluation (NEW!) ← Evaluates quality of all previous phases

### 2. Generate Evaluation Report

```bash
python scripts/generate_evaluation_report.py
```

This generates a quality report from the evaluation database.

## 📊 What Gets Created

- **Database**: `data/evaluations.db` - SQLite database with all evaluations
- **Reports**: `data/quality_reports/quality_report_TIMESTAMP.json` - JSON reports

## 🔍 Quick Database Queries (Python)

```python
from database.models import DatabaseManager
from database.queries import EvaluationQueries

# Initialize
db = DatabaseManager()
queries = EvaluationQueries(db)

# Get recent evaluations
recent = queries.get_recent_evaluations(limit=10)
print(recent)

# Get average scores by agent
avg_scores = queries.get_avg_scores_by_agent(days=7)
print(avg_scores)

# Get quality distribution
distribution = queries.get_quality_distribution()
print(distribution)

# Close connection
db.close()
```

## 📖 Full Documentation

See `EVALUATION_SYSTEM_GUIDE.md` for complete explanation of every file and concept!

