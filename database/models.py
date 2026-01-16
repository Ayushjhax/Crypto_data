
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
from pathlib import Path
import json

Base = declarative_base()


class Evaluation(Base):
    __tablename__ = 'evaluations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    agent_type = Column(String(50), nullable=False)  # nullable=False means this field is required
    
    symbol = Column(String(10))
    
    evaluation_timestamp = Column(DateTime, default=datetime.now)
    
    completeness_score = Column(Float)
    accuracy_score = Column(Float)
    consistency_score = Column(Float)
    overall_score = Column(Float)
    
    metrics_json = Column(Text)  # Stores detailed metrics as JSON
    evaluated_fields = Column(Text)  # List of fields that were checked
    issues_found = Column(Text)  # List of problems found
    recommendations = Column(Text)  # Suggestions for improvement
    
    pipeline_run_id = Column(String(100))  # Groups evaluations from same pipeline run
    data_file_path = Column(Text)  # Path to the data file that was evaluated
    evaluation_version = Column(String(20), default='1.0')  # Version of evaluation logic
    
    def to_dict(self):
        return {
            'id': self.id,
            'agent_type': self.agent_type,
            'symbol': self.symbol,
            'evaluation_timestamp': self.evaluation_timestamp.isoformat() if self.evaluation_timestamp else None,
            'completeness_score': self.completeness_score,
            'accuracy_score': self.accuracy_score,
            'consistency_score': self.consistency_score,
            'overall_score': self.overall_score,
            'metrics_json': json.loads(self.metrics_json) if self.metrics_json else None,
            'evaluated_fields': json.loads(self.evaluated_fields) if self.evaluated_fields else None,
            'issues_found': json.loads(self.issues_found) if self.issues_found else None,
            'recommendations': json.loads(self.recommendations) if self.recommendations else None,
            'pipeline_run_id': self.pipeline_run_id,
            'data_file_path': self.data_file_path,
            'evaluation_version': self.evaluation_version
        }


class EvaluationSummary(Base):
    __tablename__ = 'evaluation_summary'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    agent_type = Column(String(50), nullable=False)
    summary_date = Column(Date, nullable=False)  # Date only, not datetime
    
    avg_completeness = Column(Float)
    avg_accuracy = Column(Float)
    avg_consistency = Column(Float)
    avg_overall_score = Column(Float)
    
    total_evaluations = Column(Integer, default=0)
    high_quality_count = Column(Integer, default=0)  # overall_score > 0.8
    medium_quality_count = Column(Integer, default=0)  # 0.5 <= overall_score <= 0.8
    low_quality_count = Column(Integer, default=0)  # overall_score < 0.5
    
    top_issues = Column(Text)
    
    def to_dict(self):
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
    __tablename__ = 'pipeline_runs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    run_id = Column(String(100), unique=True, nullable=False)
    
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime)  # Set when pipeline completes
    
    status = Column(String(20), default='running')
    
    total_evaluations = Column(Integer, default=0)
    avg_overall_score = Column(Float)
    
    def to_dict(self):
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
    
    def __init__(self, db_path: str = "data/evaluations.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)
        
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        return self.SessionLocal()
    
    def close(self):
        self.engine.dispose()

