
import uuid
from datetime import datetime, date
from typing import Dict, Any, Optional
import json
from sqlalchemy import text
from database.models import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EventTracker:
    
    def __init__(self, db_path: str = "data/analytics.db"):
        self.db_manager = DatabaseManager(db_path)
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        try:
            analytics_sql = """
            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name VARCHAR(100) NOT NULL,
                user_id VARCHAR(100) DEFAULT 'default_user',
                session_id VARCHAR(100) NOT NULL,
                properties TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS analytics_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(100) UNIQUE NOT NULL,
                user_id VARCHAR(100) DEFAULT 'default_user',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                status VARCHAR(20) DEFAULT 'active',
                collection_completed INTEGER DEFAULT 0,
                cleaning_completed INTEGER DEFAULT 0,
                labeling_completed INTEGER DEFAULT 0,
                evaluation_completed INTEGER DEFAULT 0,
                coins_collected INTEGER DEFAULT 0,
                coins_cleaned INTEGER DEFAULT 0,
                coins_labeled INTEGER DEFAULT 0
            );
            
            CREATE INDEX IF NOT EXISTS idx_analytics_events_name ON analytics_events(event_name);
            CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON analytics_events(timestamp);
            CREATE INDEX IF NOT EXISTS idx_analytics_events_session ON analytics_events(session_id);
            CREATE INDEX IF NOT EXISTS idx_analytics_sessions_started ON analytics_sessions(started_at);
            CREATE INDEX IF NOT EXISTS idx_analytics_sessions_status ON analytics_sessions(status);
        Track an event.
        
        INTERVIEW EXPLANATION:
        Core method for event tracking. Stores events in database
        for later analysis.
        
        Args:
            event_name: Name of event (e.g., 'pipeline_start', 'collection_complete')
            session_id: Optional session identifier
            user_id: Optional user identifier
            properties: Optional event properties (JSON)
        
        Returns:
            session_id (creates new if not provided)
                    INSERT INTO analytics_events 
                    (event_name, user_id, session_id, properties, timestamp)
                    VALUES (:event_name, :user_id, :session_id, :properties, :timestamp)
        Start a new pipeline run session.
        
        INTERVIEW EXPLANATION:
        Tracks when a user starts running the pipeline.
        This is the start of our funnel.
        
        Returns:
            session_id for this pipeline run
                    INSERT INTO analytics_sessions 
                    (session_id, user_id, started_at, status)
                    VALUES (:session_id, :user_id, :started_at, 'active')
        Track completion of a pipeline phase.
        
        INTERVIEW EXPLANATION:
        Tracks progression through the funnel:
        - collection_complete
        - cleaning_complete
        - labeling_complete
        - evaluation_complete
        
        This enables funnel analysis.
        
        Args:
            session_id: Session identifier
            phase: Phase name ('collection', 'cleaning', 'labeling', 'evaluation')
            metadata: Optional metadata about the phase completion
                    UPDATE analytics_sessions
                    SET {phase_column} = 1
                    WHERE session_id = :session_id
                            UPDATE analytics_sessions
                            SET coins_collected = :count
                            WHERE session_id = :session_id
                            UPDATE analytics_sessions
                            SET coins_cleaned = :count
                            WHERE session_id = :session_id
                            UPDATE analytics_sessions
                            SET coins_labeled = :count
                            WHERE session_id = :session_id
        Mark pipeline session as complete.
        
        INTERVIEW EXPLANATION:
        Marks the end of a pipeline run.
        Updates session status and completion time.
        
        Args:
            session_id: Session identifier
            status: Status ('completed', 'failed')
                    UPDATE analytics_sessions
                    SET completed_at = :completed_at, status = :status
                    WHERE session_id = :session_id
        self.db_manager.close()




