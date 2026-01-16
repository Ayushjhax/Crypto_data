
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
            session = self.db_manager.get_session()
            try:
                # Create analytics_events table
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS analytics_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_name VARCHAR(100) NOT NULL,
                        user_id VARCHAR(100) DEFAULT 'default_user',
                        session_id VARCHAR(100) NOT NULL,
                        properties TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create analytics_sessions table
                session.execute(text("""
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
                    )
                """))
                
                # Create indexes
                session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_analytics_events_name ON analytics_events(event_name)
                """))
                session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON analytics_events(timestamp)
                """))
                session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_analytics_events_session ON analytics_events(session_id)
                """))
                session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_analytics_sessions_started ON analytics_sessions(started_at)
                """))
                session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_analytics_sessions_status ON analytics_sessions(status)
                """))
                
                session.commit()
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error ensuring tables exist: {e}")
            raise
    
    def track_event(self, event_name: str, session_id: Optional[str] = None, 
                    user_id: Optional[str] = None, properties: Optional[Dict[str, Any]] = None) -> str:
        """Track an event.
        
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
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if not user_id:
            user_id = 'default_user'
        
        properties_json = json.dumps(properties) if properties else None
        
        session = self.db_manager.get_session()
        try:
            query = text("""
                INSERT INTO analytics_events 
                (event_name, user_id, session_id, properties, timestamp)
                VALUES (:event_name, :user_id, :session_id, :properties, :timestamp)
            """)
            session.execute(query, {
                'event_name': event_name,
                'user_id': user_id,
                'session_id': session_id,
                'properties': properties_json,
                'timestamp': datetime.now()
            })
            session.commit()
        finally:
            session.close()
        
        return session_id
    
    def start_session(self, user_id: Optional[str] = None) -> str:
        """Start a new pipeline run session.
        
        INTERVIEW EXPLANATION:
        Tracks when a user starts running the pipeline.
        This is the start of our funnel.
        
        Returns:
            session_id for this pipeline run
        """
        session_id = str(uuid.uuid4())
        if not user_id:
            user_id = 'default_user'
        
        session = self.db_manager.get_session()
        try:
            query = text("""
                INSERT INTO analytics_sessions 
                (session_id, user_id, started_at, status)
                VALUES (:session_id, :user_id, :started_at, 'active')
            """)
            session.execute(query, {
                'session_id': session_id,
                'user_id': user_id,
                'started_at': datetime.now()
            })
            session.commit()
        finally:
            session.close()
        
        return session_id
    
    def track_phase_completion(self, session_id: str, phase: str, 
                               metadata: Optional[Dict[str, Any]] = None):
        """Track completion of a pipeline phase.
        
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
        """
        phase_column_map = {
            'collection': 'collection_completed',
            'cleaning': 'cleaning_completed',
            'labeling': 'labeling_completed',
            'evaluation': 'evaluation_completed'
        }
        
        phase_column = phase_column_map.get(phase)
        if not phase_column:
            logger.warning(f"Unknown phase: {phase}")
            return
        
        session = self.db_manager.get_session()
        try:
            query = text(f"""
                UPDATE analytics_sessions
                SET {phase_column} = 1
                WHERE session_id = :session_id
            """)
            session.execute(query, {'session_id': session_id})
            session.commit()
        finally:
            session.close()
    
    def update_coin_count(self, session_id: str, phase: str, count: int):
        """Update coin count for a phase."""
        column_map = {
            'collection': 'coins_collected',
            'cleaning': 'coins_cleaned',
            'labeling': 'coins_labeled'
        }
        
        column = column_map.get(phase)
        if not column:
            return
        
        session = self.db_manager.get_session()
        try:
            query = text(f"""
                UPDATE analytics_sessions
                SET {column} = :count
                WHERE session_id = :session_id
            """)
            session.execute(query, {'session_id': session_id, 'count': count})
            session.commit()
        finally:
            session.close()
    
    def complete_session(self, session_id: str, status: str = 'completed'):
        """Mark pipeline session as complete.
        
        INTERVIEW EXPLANATION:
        Marks the end of a pipeline run.
        Updates session status and completion time.
        
        Args:
            session_id: Session identifier
            status: Status ('completed', 'failed')
        """
        session = self.db_manager.get_session()
        try:
            query = text("""
                UPDATE analytics_sessions
                SET completed_at = :completed_at, status = :status
                WHERE session_id = :session_id
            """)
            session.execute(query, {
                'session_id': session_id,
                'completed_at': datetime.now(),
                'status': status
            })
            session.commit()
        finally:
            session.close()
    
    def start_pipeline_session(self, user_id: Optional[str] = None) -> str:
        """Wrapper for start_session to maintain compatibility."""
        return self.start_session(user_id)
    
    def complete_pipeline_session(self, session_id: str, status: str = 'completed'):
        """Wrapper for complete_session to maintain compatibility."""
        self.complete_session(session_id, status)
    
    def close(self):
        """Close database connection."""
        self.db_manager.close()




