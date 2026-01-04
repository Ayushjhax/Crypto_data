-- SQL Schema for Critic Agent Evaluation System
-- 
-- INTERVIEW EXPLANATION:
-- This SQL file defines the database schema (table structure).
-- It's good practice to have this separate file for reference,
-- even though SQLAlchemy will create tables automatically.

-- Evaluations table: Stores individual evaluations
CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_type VARCHAR(50) NOT NULL,  -- 'collector', 'cleaner', 'labeler'
    symbol VARCHAR(10),
    evaluation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Data quality metrics (scores from 0.0 to 1.0)
    completeness_score FLOAT CHECK(completeness_score >= 0 AND completeness_score <= 1),
    accuracy_score FLOAT CHECK(accuracy_score >= 0 AND accuracy_score <= 1),
    consistency_score FLOAT CHECK(consistency_score >= 0 AND consistency_score <= 1),
    overall_score FLOAT CHECK(overall_score >= 0 AND overall_score <= 1),
    
    -- Detailed metrics (JSON format stored as TEXT in SQLite)
    metrics_json TEXT,
    
    -- Evaluation details (JSON arrays stored as TEXT)
    evaluated_fields TEXT,  -- JSON array of fields evaluated
    issues_found TEXT,      -- JSON array of issues
    recommendations TEXT,   -- JSON array of recommendations
    
    -- Metadata
    pipeline_run_id VARCHAR(100),
    data_file_path TEXT,
    evaluation_version VARCHAR(20) DEFAULT '1.0'
);

-- Evaluation summary table: Daily/aggregated metrics
CREATE TABLE IF NOT EXISTS evaluation_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_type VARCHAR(50) NOT NULL,
    summary_date DATE NOT NULL,
    
    -- Aggregated scores (averages)
    avg_completeness FLOAT,
    avg_accuracy FLOAT,
    avg_consistency FLOAT,
    avg_overall_score FLOAT,
    
    -- Counts
    total_evaluations INTEGER DEFAULT 0,
    high_quality_count INTEGER DEFAULT 0,  -- overall_score > 0.8
    medium_quality_count INTEGER DEFAULT 0, -- 0.5 <= overall_score <= 0.8
    low_quality_count INTEGER DEFAULT 0,   -- overall_score < 0.5
    
    -- Common issues (JSON)
    top_issues TEXT,
    
    UNIQUE(agent_type, summary_date)
);

-- Pipeline runs tracking
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id VARCHAR(100) UNIQUE NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'running',  -- 'running', 'completed', 'failed'
    total_evaluations INTEGER DEFAULT 0,
    avg_overall_score FLOAT
);

-- Indexes for performance (make queries faster)
CREATE INDEX IF NOT EXISTS idx_evaluations_agent_type ON evaluations(agent_type);
CREATE INDEX IF NOT EXISTS idx_evaluations_timestamp ON evaluations(evaluation_timestamp);
CREATE INDEX IF NOT EXISTS idx_evaluations_symbol ON evaluations(symbol);
CREATE INDEX IF NOT EXISTS idx_evaluation_summary_date ON evaluation_summary(summary_date);
CREATE INDEX IF NOT EXISTS idx_evaluation_summary_agent ON evaluation_summary(agent_type, summary_date);

