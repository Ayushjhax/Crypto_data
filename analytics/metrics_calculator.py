
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import text
from database.models import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MetricsCalculator:
    
    def __init__(self, db_path: str = "data/analytics.db"):
        self.db_manager = DatabaseManager(db_path)
    
    def calculate_dau(self, target_date: Optional[date] = None) -> int:
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
            return row.dau if row else 0
        finally:
            session.close()
    
    def get_dau_timeseries(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get DAU for the last N days.
        
        INTERVIEW EXPLANATION:
        Returns time series data for DAU chart.
        Useful for tracking trends over time.
        
        Args:
            days: Number of days to retrieve
        
        Returns:
            List of {date, dau} dictionaries
        """
        start_date = date.today() - timedelta(days=days)
        session = self.db_manager.get_session()
        try:
            result = session.execute(
                text("""
                    SELECT DATE(started_at) as date, COUNT(DISTINCT session_id) as dau
                    FROM analytics_sessions
                    WHERE DATE(started_at) >= :start_date
                    GROUP BY DATE(started_at)
                    ORDER BY DATE(started_at)
                """),
                {'start_date': start_date}
            )
            return [{'date': str(row.date), 'dau': row.dau} for row in result.fetchall()]
        finally:
            session.close()
    
    def calculate_conversion_rate(self, start_event: str, end_event: str, 
                                  date_range: Optional[tuple] = None) -> float:
        """Calculate conversion rate between two events.
        
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
            query_params = {}
            date_filter = ""
            if date_range:
                date_filter = " AND DATE(timestamp) BETWEEN :start_date AND :end_date"
                query_params['start_date'] = date_range[0]
                query_params['end_date'] = date_range[1]
            
            # Count users who started
            start_result = session.execute(
                text(f"""
                    SELECT COUNT(DISTINCT session_id) as count
                    FROM analytics_events
                    WHERE event_name = :start_event{date_filter}
                """),
                {**query_params, 'start_event': start_event}
            )
            start_count = start_result.fetchone().count
            
            if start_count == 0:
                return 0.0
            
            # Count users who completed
            end_result = session.execute(
                text(f"""
                    SELECT COUNT(DISTINCT session_id) as count
                    FROM analytics_events
                    WHERE event_name = :end_event{date_filter}
                """),
                {**query_params, 'end_event': end_event}
            )
            end_count = end_result.fetchone().count
            
            return (end_count / start_count) * 100.0
        finally:
            session.close()
    
    def calculate_funnel(self, steps: List[str], 
                        date_range: Optional[tuple] = None) -> Dict[str, Any]:
        """Calculate funnel analysis with drop-off rates.
        
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
        session = self.db_manager.get_session()
        try:
            query_params = {}
            date_filter = ""
            if date_range:
                date_filter = " AND DATE(timestamp) BETWEEN :start_date AND :end_date"
                query_params['start_date'] = date_range[0]
                query_params['end_date'] = date_range[1]
            
            funnel_data = {}
            previous_count = None
            
            for step in steps:
                result = session.execute(
                    text(f"""
                        SELECT COUNT(DISTINCT session_id) as count
                        FROM analytics_events
                        WHERE event_name = :step{date_filter}
                    """),
                    {**query_params, 'step': step}
                )
                count = result.fetchone().count
                
                drop_off = None
                conversion_rate = None
                if previous_count is not None and previous_count > 0:
                    drop_off = ((previous_count - count) / previous_count) * 100.0
                    conversion_rate = (count / previous_count) * 100.0
                
                funnel_data[step] = {
                    'count': count,
                    'drop_off': drop_off,
                    'conversion_rate': conversion_rate
                }
                previous_count = count
            
            return funnel_data
        finally:
            session.close()
    
    def calculate_retention(self, cohort_date: date, days: List[int]) -> Dict[int, float]:
        """Calculate retention rates for a cohort.
        
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
        session = self.db_manager.get_session()
        try:
            # Get cohort users
            cohort_result = session.execute(
                text("""
                    SELECT DISTINCT user_id
                    FROM analytics_sessions
                    WHERE DATE(started_at) = :cohort_date
                """),
                {'cohort_date': cohort_date}
            )
            cohort_users = [row.user_id for row in cohort_result.fetchall()]
            
            if not cohort_users:
                return {d: 0.0 for d in days}
            
            # Calculate retention for each day
            retention = {}
            placeholders = ','.join(['?' for _ in cohort_users])
            
            for day in days:
                retention_date = cohort_date + timedelta(days=day)
                result = session.execute(
                    text(f"""
                        SELECT COUNT(DISTINCT user_id) as count
                        FROM analytics_sessions
                        WHERE user_id IN ({placeholders})
                        AND DATE(started_at) = ?
                    """),
                    [*cohort_users, retention_date]
                )
                returned_count = result.fetchone().count
                retention[day] = (returned_count / len(cohort_users)) * 100.0
            
            return retention
        finally:
            session.close()
    
    def get_pipeline_funnel(self, days: int = 30) -> Dict[str, Any]:
        """Get standard pipeline funnel.
        
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
        return self.calculate_funnel(
            ['pipeline_start', 'collection_complete', 'cleaning_complete', 
             'labeling_complete', 'evaluation_complete'],
            (start_date, end_date)
        )
    
    def get_feature_usage(self, days: int = 30) -> Dict[str, Any]:
        """Get feature usage statistics.
        
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
            # Average completion time
            avg_time_result = session.execute(
                text("""
                    SELECT 
                        AVG(JULIANDAY(completed_at) - JULIANDAY(started_at)) * 24 as avg_hours
                    FROM analytics_sessions
                    WHERE status = 'completed'
                    AND DATE(started_at) BETWEEN :start_date AND :end_date
                    AND completed_at IS NOT NULL
                """),
                {'start_date': start_date, 'end_date': end_date}
            )
            avg_hours_row = avg_time_result.fetchone()
            avg_hours = avg_hours_row.avg_hours if avg_hours_row and avg_hours_row.avg_hours else 0.0
            
            # Total sessions
            total_result = session.execute(
                text("""
                    SELECT COUNT(*) as total
                    FROM analytics_sessions
                    WHERE DATE(started_at) BETWEEN :start_date AND :end_date
                """),
                {'start_date': start_date, 'end_date': end_date}
            )
            total = total_result.fetchone().total
            
            # Completed sessions
            completed_result = session.execute(
                text("""
                    SELECT COUNT(*) as completed
                    FROM analytics_sessions
                    WHERE status = 'completed'
                    AND DATE(started_at) BETWEEN :start_date AND :end_date
                """),
                {'start_date': start_date, 'end_date': end_date}
            )
            completed = completed_result.fetchone().completed
            
            completion_rate = (completed / total * 100.0) if total > 0 else 0.0
            
            return {
                'avg_completion_hours': round(avg_hours, 2),
                'total_sessions': total,
                'completed_sessions': completed,
                'completion_rate': round(completion_rate, 2)
            }
        finally:
            session.close()
    
    def get_analytics_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get complete analytics summary.
        
        INTERVIEW EXPLANATION:
        Returns all key metrics in one response.
        Useful for dashboard overview.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with all metrics
        """
        return {
            'dau': self.calculate_dau(),
            'dau_timeseries': self.get_dau_timeseries(days),
            'pipeline_funnel': self.get_pipeline_funnel(days),
            'feature_usage': self.get_feature_usage(days)
        }
    
    def close(self):
        """Close database connection."""
        self.db_manager.close()

