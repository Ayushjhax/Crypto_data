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

-- ============================================================
-- PRODUCT ANALYTICS TABLES
-- ============================================================
-- INTERVIEW EXPLANATION:
-- These tables track user interactions and pipeline usage
-- for product analytics (DAU, conversion, funnel, retention)
-- as mentioned in product analytics job descriptions

-- Analytics events table: Track all user actions/events
CREATE TABLE IF NOT EXISTS analytics_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name VARCHAR(100) NOT NULL,  -- 'pipeline_start', 'collection_complete', etc.
    user_id VARCHAR(100) DEFAULT 'default_user',  -- Optional: track different users
    session_id VARCHAR(100) NOT NULL,  -- Track pipeline run sessions
    properties TEXT,                    -- JSON properties for the event
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics sessions table: Track pipeline runs
CREATE TABLE IF NOT EXISTS analytics_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(100) DEFAULT 'default_user',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'completed', 'failed'
    
    -- Funnel tracking
    collection_completed BOOLEAN DEFAULT 0,
    cleaning_completed BOOLEAN DEFAULT 0,
    labeling_completed BOOLEAN DEFAULT 0,
    evaluation_completed BOOLEAN DEFAULT 0,
    
    -- Metadata
    coins_collected INTEGER DEFAULT 0,
    coins_cleaned INTEGER DEFAULT 0,
    coins_labeled INTEGER DEFAULT 0
);

-- Indexes for analytics tables (make queries faster)
CREATE INDEX IF NOT EXISTS idx_analytics_events_name ON analytics_events(event_name);
CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON analytics_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_events_session ON analytics_events(session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_sessions_started ON analytics_sessions(started_at);
CREATE INDEX IF NOT EXISTS idx_analytics_sessions_status ON analytics_sessions(status);

-- ============================================================
-- ANOMALY DETECTION TABLES
-- ============================================================
-- INTERVIEW EXPLANATION:
-- These tables store detected anomalies for tracking and analysis.
-- Allows teams to track which anomalies were resolved, etc.

-- Anomalies table: Stores detected anomalies
CREATE TABLE IF NOT EXISTS anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_type VARCHAR(50) NOT NULL,  -- 'collector', 'cleaner', 'labeler'
    detection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Anomaly details
    anomaly_type VARCHAR(50),  -- 'threshold', 'statistical', 'rate_of_change'
    severity VARCHAR(20),  -- 'low', 'medium', 'high'
    
    -- Metrics
    current_value FLOAT,
    threshold_value FLOAT,
    historical_avg FLOAT,
    historical_std FLOAT,
    z_score FLOAT,
    
    -- Message and details (JSON)
    message TEXT,
    anomaly_details TEXT,  -- JSON with full anomaly data
    
    -- Status
    status VARCHAR(20) DEFAULT 'new',  -- 'new', 'acknowledged', 'resolved', 'false_positive'
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    
    -- Metadata
    check_run_id VARCHAR(100)  -- Groups anomalies from same check run
);

-- Indexes for anomaly queries
CREATE INDEX IF NOT EXISTS idx_anomalies_agent_type ON anomalies(agent_type);
CREATE INDEX IF NOT EXISTS idx_anomalies_timestamp ON anomalies(detection_timestamp);
CREATE INDEX IF NOT EXISTS idx_anomalies_severity ON anomalies(severity);
CREATE INDEX IF NOT EXISTS idx_anomalies_status ON anomalies(status);
CREATE INDEX IF NOT EXISTS idx_anomalies_check_run ON anomalies(check_run_id);

