"""
SQLAlchemy models for the evaluation system.

INTERVIEW EXPLANATION:
These models represent database tables using SQLAlchemy ORM (Object-Relational Mapping).
ORM allows us to work with databases using Python objects instead of raw SQL.

Benefits:
- Type safety: Python types map to SQL types
- Code reusability: Write queries in Python, not SQL
- Database agnostic: Same code works with SQLite, PostgreSQL, MySQL
- Relationships: Easy to define relationships between tables
"""

# Import SQLAlchemy components
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
from pathlib import Path
import json

# Base class for all models - all our table classes will inherit from this
Base = declarative_base()


class Evaluation(Base):
    """
    Model representing an individual evaluation record.
    
    INTERVIEW EXPLANATION:
    This class maps to the 'evaluations' table in the database.
    Each instance represents one evaluation of data quality.
    
    When you create an Evaluation object and save it, SQLAlchemy automatically
    converts it to a SQL INSERT statement.
    """
    # Table name in the database
    __tablename__ = 'evaluations'
    
    # Primary key: Unique identifier for each record (auto-incrementing)
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Agent type: Which agent was evaluated (collector, cleaner, or labeler)
    agent_type = Column(String(50), nullable=False)  # nullable=False means this field is required
    
    # Symbol: Crypto coin symbol (BTC, ETH, etc.)
    symbol = Column(String(10))
    
    # Timestamp: When the evaluation was performed
    evaluation_timestamp = Column(DateTime, default=datetime.now)
    
    # Score columns: Quality scores from 0.0 to 1.0
    # Completeness: Are all required fields present?
    completeness_score = Column(Float)
    # Accuracy: Are values correct and within expected ranges?
    accuracy_score = Column(Float)
    # Consistency: Is data consistent with itself and expected format?
    consistency_score = Column(Float)
    # Overall: Combined score (weighted average of the above)
    overall_score = Column(Float)
    
    # JSON fields: Store complex data as JSON strings
    # SQLite doesn't have native JSON type, so we use TEXT and convert
    metrics_json = Column(Text)  # Stores detailed metrics as JSON
    evaluated_fields = Column(Text)  # List of fields that were checked
    issues_found = Column(Text)  # List of problems found
    recommendations = Column(Text)  # Suggestions for improvement
    
    # Metadata fields
    pipeline_run_id = Column(String(100))  # Groups evaluations from same pipeline run
    data_file_path = Column(Text)  # Path to the data file that was evaluated
    evaluation_version = Column(String(20), default='1.0')  # Version of evaluation logic
    
    def to_dict(self):
        """
        Convert model to dictionary for easy serialization.
        
        INTERVIEW EXPLANATION:
        This is a helper method to convert a database record (row) into
        a Python dictionary. Useful for:
        - Converting to JSON for API responses
        - Logging
        - Testing
        """
        return {
            'id': self.id,
            'agent_type': self.agent_type,
            'symbol': self.symbol,
            # Convert datetime to ISO format string for JSON serialization
            'evaluation_timestamp': self.evaluation_timestamp.isoformat() if self.evaluation_timestamp else None,
            'completeness_score': self.completeness_score,
            'accuracy_score': self.accuracy_score,
            'consistency_score': self.consistency_score,
            'overall_score': self.overall_score,
            # Parse JSON strings back to Python objects
            'metrics_json': json.loads(self.metrics_json) if self.metrics_json else None,
            'evaluated_fields': json.loads(self.evaluated_fields) if self.evaluated_fields else None,
            'issues_found': json.loads(self.issues_found) if self.issues_found else None,
            'recommendations': json.loads(self.recommendations) if self.recommendations else None,
            'pipeline_run_id': self.pipeline_run_id,
            'data_file_path': self.data_file_path,
            'evaluation_version': self.evaluation_version
        }


class EvaluationSummary(Base):
    """
    Model representing aggregated evaluation metrics.
    
    INTERVIEW EXPLANATION:
    This table stores daily summaries to enable fast analytics.
    Instead of querying thousands of individual evaluations every time,
    we pre-aggregate data into daily summaries.
    
    This is a common database optimization pattern called "materialized views"
    or "summary tables".
    """
    __tablename__ = 'evaluation_summary'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Agent type and date identify a unique summary record
    agent_type = Column(String(50), nullable=False)
    summary_date = Column(Date, nullable=False)  # Date only, not datetime
    
    # Aggregated scores: Average of all evaluations for this agent on this date
    avg_completeness = Column(Float)
    avg_accuracy = Column(Float)
    avg_consistency = Column(Float)
    avg_overall_score = Column(Float)
    
    # Counts: How many evaluations in each quality category
    total_evaluations = Column(Integer, default=0)
    high_quality_count = Column(Integer, default=0)  # overall_score > 0.8
    medium_quality_count = Column(Integer, default=0)  # 0.5 <= overall_score <= 0.8
    low_quality_count = Column(Integer, default=0)  # overall_score < 0.5
    
    # Top issues: Most common problems found (stored as JSON)
    top_issues = Column(Text)
    
    def to_dict(self):
        """Convert summary to dictionary."""
        return {
            'id': self.id,
            'agent_type': self.agent_type,
            'summary_date': self.summary_date.isoformat() if self.summary_date else None,
            'avg_completeness': self.avg_completeness,
            'avg_accuracy': self.avg_accuracy,
            'avg_consistency': self.avg_consistency,
            'avg_overall_score': self.avg_overall_score,
            'total_evaluations': self.total_evaluations,
            'high_quality_count': self.high_quality_count,
            'medium_quality_count': self.medium_quality_count,
            'low_quality_count': self.low_quality_count,
            'top_issues': json.loads(self.top_issues) if self.top_issues else None
        }


class PipelineRun(Base):
    """
    Model representing a pipeline execution run.
    
    INTERVIEW EXPLANATION:
    Tracks each time the full pipeline runs (collection -> cleaning -> labeling).
    Useful for:
    - Tracking pipeline performance over time
    - Debugging: Find all evaluations from a specific run
    - Reporting: Compare runs
    """
    __tablename__ = 'pipeline_runs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Unique identifier for this pipeline run
    run_id = Column(String(100), unique=True, nullable=False)
    
    # Timing information
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime)  # Set when pipeline completes
    
    # Status: Track if pipeline is running, completed, or failed
    status = Column(String(20), default='running')
    
    # Summary statistics for this run
    total_evaluations = Column(Integer, default=0)
    avg_overall_score = Column(Float)
    
    def to_dict(self):
        """Convert pipeline run to dictionary."""
        return {
            'id': self.id,
            'run_id': self.run_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'total_evaluations': self.total_evaluations,
            'avg_overall_score': self.avg_overall_score
        }


class Anomaly(Base):
    """
    Model representing a detected anomaly.
    
    INTERVIEW EXPLANATION:
    Stores anomaly records for tracking and analysis.
    Allows teams to track which anomalies were resolved, etc.
    """
    __tablename__ = 'anomalies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_type = Column(String(50), nullable=False)
    detection_timestamp = Column(DateTime, default=datetime.now)
    
    anomaly_type = Column(String(50))
    severity = Column(String(20))
    
    current_value = Column(Float)
    threshold_value = Column(Float)
    historical_avg = Column(Float)
    historical_std = Column(Float)
    z_score = Column(Float)
    
    message = Column(Text)
    anomaly_details = Column(Text)  # JSON
    
    status = Column(String(20), default='new')
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    check_run_id = Column(String(100))
    
    def to_dict(self):
        """Convert anomaly to dictionary."""
        return {
            'id': self.id,
            'agent_type': self.agent_type,
            'detection_timestamp': self.detection_timestamp.isoformat() if self.detection_timestamp else None,
            'anomaly_type': self.anomaly_type,
            'severity': self.severity,
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'historical_avg': self.historical_avg,
            'historical_std': self.historical_std,
            'z_score': self.z_score,
            'message': self.message,
            'anomaly_details': json.loads(self.anomaly_details) if self.anomaly_details else None,
            'status': self.status,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'check_run_id': self.check_run_id
        }


class DatabaseManager:
    """
    Manages database connections and operations.
    
    INTERVIEW EXPLANATION:
    This class is a "singleton" pattern - manages the database connection
    and provides a clean interface for database operations.
    
    Responsibilities:
    1. Create database connection (engine)
    2. Create tables if they don't exist
    3. Provide session factory for database operations
    4. Handle connection cleanup
    """
    
    def __init__(self, db_path: str = "data/evaluations.db"):
        """
        Initialize database manager.
        
        INTERVIEW EXPLANATION:
        Args:
            db_path: Path to SQLite database file
                    SQLite stores entire database in a single file
                    Good for development, PostgreSQL/MySQL for production
        """
        # Convert to Path object for easier file manipulation
        self.db_path = Path(db_path)
        # Create parent directories if they don't exist
        # parents=True creates all parent directories
        # exist_ok=True doesn't error if directory already exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create SQLAlchemy engine
        # sqlite:/// tells SQLAlchemy to use SQLite
        # echo=False means don't print all SQL statements (set True for debugging)
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)
        
        # Create session factory
        # Sessions are like "transactions" - group related database operations
        # sessionmaker creates a factory function that returns new sessions
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create all tables defined in Base models
        # This runs CREATE TABLE IF NOT EXISTS for all our models
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """
        Get a new database session.
        
        INTERVIEW EXPLANATION:
        Sessions are used for all database operations:
        - session.add() - Add new record
        - session.query() - Query records
        - session.commit() - Save changes
        - session.rollback() - Undo changes
        
        Always close sessions when done to free resources.
        """
        return self.SessionLocal()
    
    def close(self):
        """
        Close database connection.
        
        INTERVIEW EXPLANATION:
        Clean up resources. Important for production applications
        to prevent connection leaks.
        """
        self.engine.dispose()

