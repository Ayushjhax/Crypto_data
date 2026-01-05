"""
Event tracking system for product analytics.

INTERVIEW EXPLANATION:
This module implements product analytics tracking:
- Tracks user events (pipeline runs, phase completions)
- Stores events in database for analysis
- Enables calculation of DAU, conversion, funnel, retention

Key concepts:
- Event-driven architecture
- Session tracking
- Funnel analysis
- Product metrics (DAU, conversion, retention)
"""

import uuid
from datetime import datetime, date
from typing import Dict, Any, Optional
import json
from sqlalchemy import text
from database.models import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EventTracker:
    """
    Track user events for product analytics.
    
    INTERVIEW EXPLANATION:
    This class implements event tracking similar to:
    - Google Analytics
    - Mixpanel
    - Amplitude
    
    It tracks:
    - When users start/complete pipeline phases
    - Which features are used
    - Conversion through funnel
    - User retention
    
    This enables calculation of:
    - DAU (Daily Active Users)
    - Conversion rates
    - Funnel analysis
    - Retention rates
    """
    
    def __init__(self, db_path: str = "data/analytics.db"):
        """
        Initialize event tracker with database connection.
        
        INTERVIEW EXPLANATION:
        Args:
            db_path: Path to analytics database file
        """
        self.db_manager = DatabaseManager(db_path)
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """
        Create analytics tables if they don't exist.
        
        INTERVIEW EXPLANATION:
        Uses raw SQL to create tables since we're not using SQLAlchemy models
        for analytics tables. This is a simpler approach.
        SQLite stores BOOLEAN as INTEGER (0 or 1).
        """
        try:
            # Create analytics tables using raw SQL
            # SQLite treats BOOLEAN as INTEGER internally
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
            """
            
            # Execute SQL statements
            session = self.db_manager.get_session()
            try:
                # Split and execute each statement separately
                for statement in analytics_sql.strip().split(';'):
                    statement = statement.strip()
                    if statement:
                        session.execute(text(statement))
                session.commit()
            finally:
                session.close()
        except Exception as e:
            logger.warning(f"Could not create analytics tables (may already exist): {e}")
    
    def track_event(
        self,
        event_name: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> str:
        """
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
        """
        # Generate session_id if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Store event in database
        session = self.db_manager.get_session()
        try:
            # Insert event
            session.execute(
                text("""
                    INSERT INTO analytics_events 
                    (event_name, user_id, session_id, properties, timestamp)
                    VALUES (:event_name, :user_id, :session_id, :properties, :timestamp)
                """),
                {
                    'event_name': event_name,
                    'user_id': user_id or 'default_user',
                    'session_id': session_id,
                    'properties': json.dumps(properties or {}),
                    'timestamp': datetime.now()
                }
            )
            session.commit()
            logger.debug(f"Tracked event: {event_name} (session: {session_id})")
        except Exception as e:
            session.rollback()
            logger.error(f"Error tracking event: {e}")
        finally:
            session.close()
        
        return session_id
    
    def start_pipeline_session(
        self,
        user_id: Optional[str] = None
    ) -> str:
        """
        Start a new pipeline run session.
        
        INTERVIEW EXPLANATION:
        Tracks when a user starts running the pipeline.
        This is the start of our funnel.
        
        Returns:
            session_id for this pipeline run
        """
        session_id = str(uuid.uuid4())
        
        session = self.db_manager.get_session()
        try:
            # Create session record
            session.execute(
                text("""
                    INSERT INTO analytics_sessions 
                    (session_id, user_id, started_at, status)
                    VALUES (:session_id, :user_id, :started_at, 'active')
                """),
                {
                    'session_id': session_id,
                    'user_id': user_id or 'default_user',
                    'started_at': datetime.now()
                }
            )
            session.commit()
            
            # Track event
            self.track_event('pipeline_start', session_id, user_id)
            
            logger.info(f"Started pipeline session: {session_id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error starting session: {e}")
        finally:
            session.close()
        
        return session_id
    
    def track_phase_completion(
        self,
        session_id: str,
        phase: str,  # 'collection', 'cleaning', 'labeling', 'evaluation'
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
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
        """
        # Update session record
        phase_column = f"{phase}_completed"
        
        session = self.db_manager.get_session()
        try:
            # Update session
            session.execute(
                text(f"""
                    UPDATE analytics_sessions
                    SET {phase_column} = 1
                    WHERE session_id = :session_id
                """),
                {'session_id': session_id}
            )
            
            # Update metadata if provided
            if metadata:
                if phase == 'collection':
                    session.execute(
                        text("""
                            UPDATE analytics_sessions
                            SET coins_collected = :count
                            WHERE session_id = :session_id
                        """),
                        {'session_id': session_id, 'count': metadata.get('coins_count', 0)}
                    )
                elif phase == 'cleaning':
                    session.execute(
                        text("""
                            UPDATE analytics_sessions
                            SET coins_cleaned = :count
                            WHERE session_id = :session_id
                        """),
                        {'session_id': session_id, 'count': metadata.get('files_cleaned', 0)}
                    )
                elif phase == 'labeling':
                    session.execute(
                        text("""
                            UPDATE analytics_sessions
                            SET coins_labeled = :count
                            WHERE session_id = :session_id
                        """),
                        {'session_id': session_id, 'count': metadata.get('records_labeled', 0)}
                    )
            
            session.commit()
            
            # Track event
            self.track_event(
                f'{phase}_complete',
                session_id,
                properties=metadata
            )
            
            logger.info(f"Tracked {phase} completion for session: {session_id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error tracking phase completion: {e}")
        finally:
            session.close()
    
    def complete_pipeline_session(self, session_id: str, status: str = 'completed'):
        """
        Mark pipeline session as complete.
        
        INTERVIEW EXPLANATION:
        Marks the end of a pipeline run.
        Updates session status and completion time.
        
        Args:
            session_id: Session identifier
            status: Status ('completed', 'failed')
        """
        session = self.db_manager.get_session()
        try:
            session.execute(
                text("""
                    UPDATE analytics_sessions
                    SET completed_at = :completed_at, status = :status
                    WHERE session_id = :session_id
                """),
                {
                    'session_id': session_id,
                    'completed_at': datetime.now(),
                    'status': status
                }
            )
            session.commit()
            
            self.track_event('pipeline_complete', session_id)
            logger.info(f"Completed pipeline session: {session_id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error completing session: {e}")
        finally:
            session.close()
    
    def close(self):
        """Close database connection."""
        self.db_manager.close()




