# Critic Agent Evaluation System - Complete Guide

## 📚 Overview

This document explains the **Critic Agent Evaluation System** that has been added to DonutAI. This system evaluates data quality from all pipeline stages (collection, cleaning, labeling) and stores evaluation results in a SQL database for analysis.

## 🎯 What is a Critic Agent?

A **Critic Agent** is an AI/ML pattern where:
1. **Primary Agents** perform tasks (collect data, clean data, label data)
2. **Critic Agent** evaluates the quality of their outputs
3. **Evaluation results** are stored and analyzed to improve the pipeline

Think of it like a quality control inspector in a factory - they don't make products, they check if products meet quality standards.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     DATA PIPELINE                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Phase 1: Collector Agent  ──┐                              │
│    ↓ Collects crypto data     │                              │
│                               │                              │
│  Phase 2: Cleaner Agent  ─────┼──┐                           │
│    ↓ Cleans data              │  │                           │
│                               │  │                           │
│  Phase 3: Labeler Agent  ─────┼──┼──┐                        │
│    ↓ Adds labels              │  │  │                        │
│                               │  │  │                        │
│  Phase 4: Evaluator Agent  ───┼──┼──┼──┐                     │
│    ↓ Evaluates quality        │  │  │  │                     │
│                               │  │  │  │                     │
│                               ↓  ↓  ↓  ↓                     │
│                    ┌──────────────────────┐                  │
│                    │  SQLite Database     │                  │
│                    │  (evaluations.db)    │                  │
│                    └──────────────────────┘                  │
│                               │                              │
│                               ↓                              │
│                    ┌──────────────────────┐                  │
│                    │  Analytics & Reports │                  │
│                    └──────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## 📁 File Structure

```
DonutAI/
├── database/                          # Database layer
│   ├── __init__.py                   # Package initialization
│   ├── schema.sql                    # SQL schema definition
│   ├── models.py                     # SQLAlchemy ORM models
│   └── queries.py                    # SQL queries for analytics
│
├── core/
│   └── data_evaluator.py             # Core evaluation logic (critic)
│
├── agents/
│   └── evaluator_agent.py            # Evaluator agent (orchestration)
│
├── analytics/
│   ├── __init__.py
│   └── evaluation_analyzer.py        # Report generation
│
├── scripts/
│   └── generate_evaluation_report.py # Report script
│
└── data/
    └── evaluations.db                # SQLite database (created automatically)
```

## 🔍 Detailed Explanation by File

### 1. `database/schema.sql`

**Purpose**: SQL schema definition (reference document)

**Key Concepts**:
- **CREATE TABLE**: Defines table structure
- **PRIMARY KEY**: Unique identifier for each row
- **CHECK constraints**: Validates data (e.g., scores 0.0-1.0)
- **INDEXES**: Speed up queries
- **JSON storage**: SQLite stores JSON as TEXT, we parse it in Python

**Three Main Tables**:
1. **evaluations**: Individual evaluation records
2. **evaluation_summary**: Daily aggregated metrics
3. **pipeline_runs**: Track pipeline executions

---

### 2. `database/models.py`

**Purpose**: Python objects that map to database tables (ORM - Object-Relational Mapping)

**Key Concepts**:

#### SQLAlchemy ORM
```python
# Instead of writing SQL:
# INSERT INTO evaluations (agent_type, symbol, overall_score) VALUES ('collector', 'BTC', 0.85)

# We write Python:
eval_record = Evaluation(agent_type='collector', symbol='BTC', overall_score=0.85)
session.add(eval_record)
session.commit()
```

#### Base Classes
- `Base = declarative_base()`: All models inherit from this
- SQLAlchemy automatically creates tables from these classes

#### Model Classes
- **Evaluation**: Individual evaluation record
- **EvaluationSummary**: Aggregated daily metrics
- **PipelineRun**: Pipeline execution tracking

#### DatabaseManager
- Manages database connection
- Creates tables automatically
- Provides sessions for database operations

**Why ORM?**:
- Type safety (Python types → SQL types)
- Database agnostic (same code works with SQLite, PostgreSQL, MySQL)
- Less SQL to write
- Better error handling

---

### 3. `database/queries.py`

**Purpose**: SQL queries for analytics (both SQLAlchemy and raw SQL)

**Key Concepts**:

#### SQLAlchemy Queries
```python
# Query with filters and ordering
query = session.query(Evaluation)
query = query.filter(Evaluation.agent_type == 'collector')
query = query.order_by(Evaluation.evaluation_timestamp.desc())
results = query.all()
```

#### Aggregation Functions
- `func.avg()`: Calculate average
- `func.count()`: Count records
- `func.sum()`: Sum values

#### Raw SQL
```python
# Sometimes raw SQL is clearer for complex queries
query = """
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN overall_score >= 0.8 THEN 1 ELSE 0 END) as high_quality
    FROM evaluations
"""
```

**Query Methods**:
- `get_recent_evaluations()`: Get recent evaluations
- `get_avg_scores_by_agent()`: Average scores per agent type
- `get_quality_distribution()`: Count high/medium/low quality
- `get_trend_over_time()`: Daily trends
- `get_top_issues()`: Most common issues

---

### 4. `core/data_evaluator.py`

**Purpose**: Core evaluation logic - the "critic" that assesses data quality

**Key Concepts**:

#### Evaluation Dimensions
1. **Completeness**: Are required fields present?
   - Score = (fields present / total required fields)
   - Example: 3 out of 4 fields = 0.75 score

2. **Accuracy**: Are values correct and reasonable?
   - Checks: Negative prices, unrealistic values, NaN/Inf
   - Each issue reduces score

3. **Consistency**: Does data make sense together?
   - Checks: Label matches data, format is correct
   - Example: price_movement label should match price_change_24h value

4. **Overall Score**: Weighted average
   - Completeness: 40% weight
   - Accuracy: 40% weight
   - Consistency: 20% weight

#### Evaluation Methods
- `evaluate_collector_data()`: Evaluates raw collected data
- `evaluate_cleaner_data()`: Evaluates cleaned data
- `evaluate_labeler_data()`: Evaluates labeled data

#### Scoring Example
```python
# Completeness: 3/4 fields present = 0.75
completeness_score = 0.75

# Accuracy: 1 issue found, reduce by 0.2 = 0.8
accuracy_score = 0.8

# Consistency: No issues = 1.0
consistency_score = 1.0

# Overall: Weighted average
overall_score = (0.75 * 0.4) + (0.8 * 0.4) + (1.0 * 0.2) = 0.82
```

---

### 5. `agents/evaluator_agent.py`

**Purpose**: Orchestrates the evaluation workflow

**Key Concepts**:

#### Agent Pattern
- **Orchestration**: Coordinates workflow
- **Separation of Concerns**: Agent orchestrates, core module does logic
- **Error Handling**: Continues processing even if some evaluations fail

#### Workflow
1. Start pipeline run (create unique run ID)
2. Evaluate all files from each stage:
   - Load JSON data
   - Call evaluator
   - Save to database
3. Track statistics
4. Generate summary

#### Methods
- `evaluate_collector_output()`: Evaluate one collector output
- `evaluate_cleaner_output()`: Evaluate one cleaner output
- `evaluate_labeler_output()`: Evaluate one labeler output
- `evaluate_all_pipeline_outputs()`: Batch evaluate all files
- `_save_evaluation()`: Private method to save to database

#### Database Operations
```python
# Get session
session = self.db_manager.get_session()

# Create record
eval_record = Evaluation(agent_type='collector', symbol='BTC', ...)

# Add to session (stage for insert)
session.add(eval_record)

# Commit (actually execute INSERT)
session.commit()

# Always close session
session.close()
```

---

### 6. `analytics/evaluation_analyzer.py`

**Purpose**: Generates reports and analytics from evaluation data

**Key Concepts**:

#### Report Generation
1. Query database for evaluations
2. Aggregate data (averages, counts, trends)
3. Generate recommendations
4. Export to JSON

#### Report Structure
```json
{
  "generated_at": "2024-01-15T10:30:00",
  "period_days": 30,
  "summary": {
    "average_scores": [...],
    "quality_distribution": {...}
  },
  "trends": {...},
  "issues": {...},
  "recommendations": [...]
}
```

#### Key Methods
- `generate_quality_report()`: Main report generation
- `_generate_recommendations_from_report()`: Business logic for recommendations
- `export_report_json()`: Save report to file

---

### 7. `scripts/generate_evaluation_report.py`

**Purpose**: Standalone script to generate reports

**Usage**:
```bash
python scripts/generate_evaluation_report.py
```

**What it does**:
1. Creates analyzer
2. Generates report for last 30 days
3. Exports to JSON file
4. Prints summary to console

---

### 8. Integration in `main.py`

**Added Phase 4**:
```python
# Phase 4: DATA EVALUATION (Critic Agent)
evaluator_agent = EvaluatorAgent()
evaluation_results = evaluator_agent.evaluate_all_pipeline_outputs()
evaluator_agent.close()
```

**Flow**:
1. Pipeline runs (collect → clean → label)
2. Evaluator evaluates all outputs
3. Results saved to database
4. Summary printed

---

## 📊 Database Schema Details

### evaluations table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key (auto-increment) |
| agent_type | VARCHAR(50) | 'collector', 'cleaner', or 'labeler' |
| symbol | VARCHAR(10) | Crypto symbol (BTC, ETH, etc.) |
| completeness_score | FLOAT | 0.0 to 1.0 |
| accuracy_score | FLOAT | 0.0 to 1.0 |
| consistency_score | FLOAT | 0.0 to 1.0 |
| overall_score | FLOAT | 0.0 to 1.0 |
| metrics_json | TEXT | JSON string with detailed metrics |
| issues_found | TEXT | JSON array of issues |
| recommendations | TEXT | JSON array of recommendations |
| pipeline_run_id | VARCHAR(100) | Groups evaluations from same run |
| evaluation_timestamp | TIMESTAMP | When evaluation was performed |

### Example Query
```sql
-- Get average scores by agent type for last 7 days
SELECT 
    agent_type,
    AVG(overall_score) as avg_score,
    COUNT(*) as total
FROM evaluations
WHERE evaluation_timestamp >= datetime('now', '-7 days')
GROUP BY agent_type;
```

---

## 🚀 How to Use

### 1. Run Pipeline (includes evaluation)
```bash
python main.py
```

This will:
- Collect data (Phase 1)
- Clean data (Phase 2)
- Label data (Phase 3)
- Evaluate data (Phase 4) ← NEW!
- Save evaluations to `data/evaluations.db`

### 2. Generate Report
```bash
python scripts/generate_evaluation_report.py
```

This will:
- Query evaluation database
- Generate quality report
- Save to `data/quality_reports/quality_report_TIMESTAMP.json`
- Print summary to console

### 3. Query Database Directly
```python
from database.models import DatabaseManager
from database.queries import EvaluationQueries

db = DatabaseManager()
queries = EvaluationQueries(db)

# Get recent evaluations
recent = queries.get_recent_evaluations(limit=10)

# Get average scores
avg_scores = queries.get_avg_scores_by_agent(days=7)

# Get quality distribution
distribution = queries.get_quality_distribution()
```

---

## 🎓 Key Learning Points for Interviews

### 1. **Critic Agent Pattern**
- Explain: Primary agents do work, critic agent evaluates quality
- Use case: Quality control, monitoring, improvement

### 2. **Database Design**
- **Normalization**: Separate tables for evaluations, summaries, runs
- **Indexing**: Indexes on frequently queried columns
- **JSON Storage**: Storing complex data as JSON in SQLite

### 3. **ORM vs Raw SQL**
- **ORM (SQLAlchemy)**: Type-safe, database-agnostic, less SQL
- **Raw SQL**: More control, complex queries, direct SQL knowledge
- **Both have their place**: Use ORM for CRUD, raw SQL for complex analytics

### 4. **Data Processing Pipeline**
- **ETL**: Extract (collect) → Transform (clean, label) → Load (evaluate, store)
- **Batch Processing**: Process multiple files in one operation
- **Error Handling**: Continue processing even if some items fail

### 5. **Analytics & Reporting**
- **Aggregation**: Calculate averages, counts, percentages
- **Trend Analysis**: Time-series data analysis
- **Recommendations**: Convert data insights into actionable recommendations

### 6. **Python Skills Demonstrated**
- **Classes & OOP**: Models, agents, analyzers
- **Database Operations**: SQLAlchemy, sessions, transactions
- **Data Processing**: JSON parsing, aggregations, statistics
- **Error Handling**: Try/except, logging, graceful degradation
- **File I/O**: Reading/writing JSON, path management

### 7. **SQL Skills Demonstrated**
- **Schema Design**: Tables, columns, constraints, indexes
- **Queries**: SELECT, WHERE, GROUP BY, ORDER BY
- **Aggregations**: AVG, COUNT, SUM
- **Conditional Logic**: CASE statements
- **Joins**: (Can be added for more complex queries)

---

## 🔧 Troubleshooting

### Database not created
- Check that `data/` directory exists
- Check file permissions
- Database is created automatically on first use

### Import errors
```bash
# Install dependencies
pip install -r requirements.txt
```

### No evaluation data
- Run pipeline first: `python main.py`
- Check that data files exist in `data/raw/`, `data/cleaned/`, `data/labeled/`

### Database locked
- Close all database connections
- SQLite doesn't support concurrent writes well
- For production, use PostgreSQL

---

## 📈 Next Steps / Enhancements

1. **Visualizations**: Add charts/graphs to reports
2. **Real-time Monitoring**: Dashboard showing live quality metrics
3. **Alerting**: Notify when quality drops below threshold
4. **Machine Learning**: Use evaluations to train models to predict quality
5. **PostgreSQL**: Migrate from SQLite to PostgreSQL for production
6. **API Endpoint**: Create REST API to query evaluations
7. **Web Dashboard**: Web UI to view reports and metrics

---

## 📝 Interview Talking Points

When discussing this project:

1. **Architecture**: "I implemented a critic agent pattern where an evaluator agent assesses data quality from three pipeline stages..."

2. **Database Design**: "I designed a normalized schema with three tables - evaluations for individual records, summaries for daily aggregates, and runs for tracking pipeline executions..."

3. **SQL Skills**: "I used both SQLAlchemy ORM and raw SQL - ORM for CRUD operations and raw SQL for complex aggregations with CASE statements..."

4. **Data Processing**: "The evaluator scores data on three dimensions - completeness, accuracy, and consistency - then stores results in a database for analytics..."

5. **Analytics**: "I built an analytics module that queries the database, aggregates metrics, identifies trends, and generates actionable recommendations..."

---

## ✅ Summary

You now have a complete **Critic Agent Evaluation System** that:

- ✅ Evaluates data quality from all pipeline stages
- ✅ Stores evaluations in SQL database
- ✅ Provides analytics and reporting
- ✅ Demonstrates SQL and Python data processing skills
- ✅ Shows database design and query optimization
- ✅ Implements professional software patterns

This is exactly what employers look for in data processing roles! 🎉

