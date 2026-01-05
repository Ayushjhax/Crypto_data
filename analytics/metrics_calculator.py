"""
Calculate product analytics metrics.

INTERVIEW EXPLANATION:
This module calculates key product metrics:
- DAU (Daily Active Users)
- Conversion rates
- Funnel analysis
- Retention rates

These are the exact metrics mentioned in product analytics job descriptions:
- DAU: Daily Active Users
- Conversion: % of users completing each step
- Funnel: Drop-off at each step
- Retention: Users returning over time (Day 1, 7, 30)
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import text
from database.models import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MetricsCalculator:
    """
    Calculate product analytics metrics.
    
    INTERVIEW EXPLANATION:
    This class implements the metrics mentioned in product analytics job descriptions:
    - DAU: Daily Active Users (unique pipeline runs per day)
    - Conversion: % of users completing each funnel step
    - Funnel: Drop-off at each step
    - Retention: Users returning over time (Day 1, 7, 30)
    """
    
    def __init__(self, db_path: str = "data/analytics.db"):
        """
        Initialize metrics calculator.
        
        INTERVIEW EXPLANATION:
        Args:
            db_path: Path to analytics database
        """
        self.db_manager = DatabaseManager(db_path)
    
    def calculate_dau(self, target_date: Optional[date] = None) -> int:
        """
        Calculate Daily Active Users (DAU).
        
        INTERVIEW EXPLANATION:
        DAU = Number of unique pipeline runs on a given day.
        This is a key product metric showing daily engagement.
        
        Args:
            target_date: Date to calculate DAU for (default: today)
        
        Returns:
            Number of unique sessions (pipeline runs) on that day
        """
        if not target_date:
            target_date = date.today()
        
        session = self.db_manager.get_session()
        try:
            result = session.execute(
                text("""
                    SELECT COUNT(DISTINCT session_id) as dau
                    FROM analytics_sessions
                    WHERE DATE(started_at) = :target_date
                """),
                {'target_date': target_date}
            )
            row = result.fetchone()
            return row[0] if row else 0
        finally:
            session.close()
    
    def get_dau_timeseries(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get DAU for the last N days.
        
        INTERVIEW EXPLANATION:
        Returns time series data for DAU chart.
        Useful for tracking trends over time.
        
        Args:
            days: Number of days to retrieve
        
        Returns:
            List of {date, dau} dictionaries
        """
        timeseries = []
        today = date.today()
        
        for i in range(days):
            target_date = today - timedelta(days=i)
            dau = self.calculate_dau(target_date)
            timeseries.append({
                'date': target_date.isoformat(),
                'dau': dau
            })
        
        return list(reversed(timeseries))  # Oldest to newest
    
    def calculate_conversion_rate(
        self,
        start_event: str,
        end_event: str,
        date_range: Optional[tuple] = None
    ) -> float:
        """
        Calculate conversion rate between two events.
        
        INTERVIEW EXPLANATION:
        Conversion rate = (users who completed end_event / users who started start_event) * 100
        
        Example:
        - start_event: 'pipeline_start'
        - end_event: 'evaluation_complete'
        - Returns: % of users who complete full pipeline
        
        Args:
            start_event: Starting event name
            end_event: Ending event name
            date_range: Optional (start_date, end_date) tuple
        
        Returns:
            Conversion rate as percentage (0-100)
        """
        session = self.db_manager.get_session()
        try:
            # Count users who started
            start_query = """
                SELECT COUNT(DISTINCT session_id)
                FROM analytics_events
                WHERE event_name = :start_event
            """
            params = {'start_event': start_event}
            
            if date_range:
                start_query += " AND DATE(timestamp) BETWEEN :start_date AND :end_date"
                params['start_date'] = date_range[0]
                params['end_date'] = date_range[1]
            
            result = session.execute(text(start_query), params)
            started = result.fetchone()[0] or 0
            
            # Count users who completed
            end_query = """
                SELECT COUNT(DISTINCT session_id)
                FROM analytics_events
                WHERE event_name = :end_event
            """
            params = {'end_event': end_event}
            
            if date_range:
                end_query += " AND DATE(timestamp) BETWEEN :start_date AND :end_date"
                params['start_date'] = date_range[0]
                params['end_date'] = date_range[1]
            
            result = session.execute(text(end_query), params)
            completed = result.fetchone()[0] or 0
            
            # Calculate conversion rate
            if started > 0:
                return round((completed / started) * 100, 2)
            return 0.0
        finally:
            session.close()
    
    def calculate_funnel(
        self,
        steps: List[str],
        date_range: Optional[tuple] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate funnel analysis with drop-off rates.
        
        INTERVIEW EXPLANATION:
        Funnel analysis shows:
        - How many users reach each step
        - Drop-off rate between steps
        - Conversion rate at each step
        
        This is critical for identifying where users drop off.
        
        Args:
            steps: List of event names in order (e.g., ['pipeline_start', 'collection_complete', ...])
            date_range: Optional (start_date, end_date) tuple
        
        Returns:
            Dictionary with funnel data for each step
        """
        funnel = {}
        previous_count = None
        
        session = self.db_manager.get_session()
        try:
            for i, step in enumerate(steps):
                # Count unique sessions that reached this step
                query = """
                    SELECT COUNT(DISTINCT session_id)
                    FROM analytics_events
                    WHERE event_name = :step
                """
                params = {'step': step}
                
                if date_range:
                    query += " AND DATE(timestamp) BETWEEN :start_date AND :end_date"
                    params['start_date'] = date_range[0]
                    params['end_date'] = date_range[1]
                
                result = session.execute(text(query), params)
                count = result.fetchone()[0] or 0
                
                # Calculate drop-off from previous step
                if previous_count is not None and previous_count > 0:
                    dropoff_rate = round(((previous_count - count) / previous_count) * 100, 2)
                    conversion_rate = round((count / previous_count) * 100, 2)
                else:
                    dropoff_rate = 0.0
                    conversion_rate = 100.0 if count > 0 else 0.0
                
                funnel[step] = {
                    'step_number': i + 1,
                    'users_reached': count,
                    'dropoff_rate': dropoff_rate,
                    'conversion_rate': conversion_rate
                }
                
                previous_count = count
            
            return funnel
        finally:
            session.close()
    
    def calculate_retention(
        self,
        cohort_date: date,
        days: List[int] = [1, 7, 30]
    ) -> Dict[str, float]:
        """
        Calculate retention rates for a cohort.
        
        INTERVIEW EXPLANATION:
        Retention = % of users who return after N days.
        
        Example:
        - Cohort: Users who ran pipeline on Jan 1
        - Day 1 retention: % who ran pipeline again on Jan 2
        - Day 7 retention: % who ran pipeline again on Jan 8
        - Day 30 retention: % who ran pipeline again on Jan 31
        
        This shows user engagement over time.
        
        Args:
            cohort_date: Date of first pipeline run (cohort date)
            days: List of days to calculate retention for
        
        Returns:
            Dictionary with retention rates for each day
        """
        retention = {}
        
        session = self.db_manager.get_session()
        try:
            # Get users in cohort (first pipeline run on cohort_date)
            cohort_query = """
                SELECT DISTINCT user_id
                FROM analytics_sessions
                WHERE DATE(started_at) = :cohort_date
            """
            result = session.execute(
                text(cohort_query),
                {'cohort_date': cohort_date}
            )
            cohort_users = [row[0] for row in result.fetchall()]
            
            if not cohort_users:
                return {f'day_{day}': 0.0 for day in days}
            
            cohort_size = len(cohort_users)
            
            # Calculate retention for each day
            for day in days:
                target_date = cohort_date + timedelta(days=day)
                
                # Count cohort users who were active on target_date
                # Use a subquery approach for SQLite
                if cohort_users:
                    placeholders = ','.join(['?' for _ in cohort_users])
                    retention_query = f"""
                        SELECT COUNT(DISTINCT user_id)
                        FROM analytics_sessions
                        WHERE user_id IN ({placeholders})
                        AND DATE(started_at) = ?
                    """
                    
                    params = list(cohort_users) + [target_date]
                    result = session.execute(text(retention_query), params)
                    active_count = result.fetchone()[0] or 0
                else:
                    active_count = 0
                
                retention_rate = round((active_count / cohort_size) * 100, 2) if cohort_size > 0 else 0.0
                retention[f'day_{day}'] = retention_rate
            
            return retention
        finally:
            session.close()
    
    def get_pipeline_funnel(self, days: int = 30) -> Dict[str, Dict[str, Any]]:
        """
        Get standard pipeline funnel.
        
        INTERVIEW EXPLANATION:
        Returns funnel for the standard DonutAI pipeline:
        1. Pipeline Start
        2. Collection Complete
        3. Cleaning Complete
        4. Labeling Complete
        5. Evaluation Complete
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Funnel dictionary
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        steps = [
            'pipeline_start',
            'collection_complete',
            'cleaning_complete',
            'labeling_complete',
            'evaluation_complete'
        ]
        
        return self.calculate_funnel(steps, (start_date, end_date))
    
    def get_feature_usage(self, days: int = 30) -> Dict[str, Any]:
        """
        Get feature usage statistics.
        
        INTERVIEW EXPLANATION:
        Shows which features are used most:
        - Average pipeline completion time
        - Completion rate
        - Total sessions
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with feature usage stats
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        session = self.db_manager.get_session()
        try:
            # Get average completion time
            completion_query = """
                SELECT 
                    AVG(JULIANDAY(completed_at) - JULIANDAY(started_at)) * 24 as avg_hours
                FROM analytics_sessions
                WHERE status = 'completed'
                AND DATE(started_at) BETWEEN :start_date AND :end_date
                AND completed_at IS NOT NULL
            """
            result = session.execute(
                text(completion_query),
                {'start_date': start_date, 'end_date': end_date}
            )
            avg_hours = result.fetchone()[0] or 0
            
            # Get completion rate
            total_query = """
                SELECT COUNT(*) as total
                FROM analytics_sessions
                WHERE DATE(started_at) BETWEEN :start_date AND :end_date
            """
            result = session.execute(
                text(total_query),
                {'start_date': start_date, 'end_date': end_date}
            )
            total_sessions = result.fetchone()[0] or 0
            
            completed_query = """
                SELECT COUNT(*) as completed
                FROM analytics_sessions
                WHERE status = 'completed'
                AND DATE(started_at) BETWEEN :start_date AND :end_date
            """
            result = session.execute(
                text(completed_query),
                {'start_date': start_date, 'end_date': end_date}
            )
            completed_sessions = result.fetchone()[0] or 0
            
            completion_rate = round((completed_sessions / total_sessions) * 100, 2) if total_sessions > 0 else 0.0
            
            return {
                'avg_completion_hours': round(avg_hours, 2) if avg_hours else 0.0,
                'total_sessions': total_sessions,
                'completed_sessions': completed_sessions,
                'completion_rate': completion_rate
            }
        finally:
            session.close()
    
    def get_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get complete analytics summary.
        
        INTERVIEW EXPLANATION:
        Returns all key metrics in one response.
        Useful for dashboard overview.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with all metrics
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        date_range = (start_date, end_date)
        
        return {
            'dau': {
                'current': self.calculate_dau(),
                'timeseries': self.get_dau_timeseries(days)
            },
            'funnel': self.get_pipeline_funnel(days),
            'conversion': {
                'pipeline_completion': self.calculate_conversion_rate(
                    'pipeline_start', 'evaluation_complete', date_range
                ),
                'collection_to_cleaning': self.calculate_conversion_rate(
                    'collection_complete', 'cleaning_complete', date_range
                ),
                'cleaning_to_labeling': self.calculate_conversion_rate(
                    'cleaning_complete', 'labeling_complete', date_range
                ),
                'labeling_to_evaluation': self.calculate_conversion_rate(
                    'labeling_complete', 'evaluation_complete', date_range
                )
            },
            'feature_usage': self.get_feature_usage(days),
            'generated_at': datetime.now().isoformat()
        }
    
    def close(self):
        """Close database connection."""
        self.db_manager.close()

