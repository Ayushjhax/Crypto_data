"""
SQL queries for evaluation analytics.

INTERVIEW EXPLANATION:
This module contains both raw SQL queries and SQLAlchemy-based queries.
Demonstrates both approaches:
- Raw SQL: More control, complex queries, direct SQL knowledge
- SQLAlchemy: More Pythonic, type-safe, database-agnostic

Both approaches have their place in real-world applications.
"""

# Import SQLAlchemy functions for query building
from sqlalchemy import func, and_, or_, text
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from database.models import Evaluation, EvaluationSummary, PipelineRun, DatabaseManager


class EvaluationQueries:
    """
    Query class for evaluation data.
    
    INTERVIEW EXPLANATION:
    This class encapsulates all database queries related to evaluations.
    Centralizes query logic for:
    - Maintainability: All queries in one place
    - Reusability: Use same queries from multiple places
    - Testing: Easy to test queries in isolation
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize with database manager.
        
        INTERVIEW EXPLANATION:
        db_manager: Provides database connection/sessions
        We store it so we can create sessions when needed
        """
        self.db = db_manager
    
    def get_recent_evaluations(self, agent_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Get recent evaluations using SQLAlchemy.
        
        INTERVIEW EXPLANATION:
        This method demonstrates SQLAlchemy query building:
        1. session.query(Evaluation) - Start query from Evaluation table
        2. .filter() - Add WHERE conditions
        3. .order_by() - Sort results (DESC = descending, newest first)
        4. .limit() - Limit number of results
        5. .all() - Execute query and get all results
        
        Equivalent SQL:
        SELECT * FROM evaluations 
        WHERE agent_type = ? (if specified)
        ORDER BY evaluation_timestamp DESC 
        LIMIT 100
        
        Args:
            agent_type: Optional filter by agent type (collector/cleaner/labeler)
            limit: Maximum number of records to return
        
        Returns:
            List of evaluation dictionaries
        """
        # Get a new database session
        session = self.db.get_session()
        try:
            # Start building query - SELECT * FROM evaluations
            query = session.query(Evaluation)
            
            # Add WHERE clause if agent_type specified
            # This is equivalent to: WHERE agent_type = agent_type
            if agent_type:
                query = query.filter(Evaluation.agent_type == agent_type)
            
            # Add ORDER BY and LIMIT
            # DESC means descending (newest first)
            query = query.order_by(Evaluation.evaluation_timestamp.desc()).limit(limit)
            
            # Execute query and convert results to dictionaries
            # .all() executes the query and returns all matching records
            return [e.to_dict() for e in query.all()]
        finally:
            # Always close session to free database connection
            session.close()
    
    def get_avg_scores_by_agent(self, days: int = 7) -> List[Dict]:
        """
        Get average scores grouped by agent type for last N days.
        
        INTERVIEW EXPLANATION:
        This demonstrates SQL aggregation functions:
        - func.avg() - Calculate average (SQL AVG function)
        - func.count() - Count records (SQL COUNT function)
        - .group_by() - Group results by agent_type
        - .filter() - Filter by date
        
        Equivalent SQL:
        SELECT 
            agent_type,
            AVG(completeness_score) as avg_completeness,
            AVG(accuracy_score) as avg_accuracy,
            AVG(consistency_score) as avg_consistency,
            AVG(overall_score) as avg_overall,
            COUNT(id) as total_count
        FROM evaluations
        WHERE evaluation_timestamp >= cutoff_date
        GROUP BY agent_type
        
        Args:
            days: Number of days to look back
        
        Returns:
            List of dictionaries with aggregated scores per agent type
        """
        session = self.db.get_session()
        try:
            # Calculate cutoff date (days ago)
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Build aggregation query
            # session.query() with multiple columns creates a SELECT with multiple columns
            results = session.query(
                Evaluation.agent_type,  # Column to group by
                func.avg(Evaluation.completeness_score).label('avg_completeness'),  # AVG() function
                func.avg(Evaluation.accuracy_score).label('avg_accuracy'),
                func.avg(Evaluation.consistency_score).label('avg_consistency'),
                func.avg(Evaluation.overall_score).label('avg_overall'),
                func.count(Evaluation.id).label('total_count')  # COUNT() function
            ).filter(
                # WHERE evaluation_timestamp >= cutoff_date
                Evaluation.evaluation_timestamp >= cutoff_date
            ).group_by(
                # GROUP BY agent_type
                Evaluation.agent_type
            ).all()  # Execute query
            
            # Convert results to dictionaries
            # results is a list of Row objects, we access columns by name
            return [
                {
                    'agent_type': r.agent_type,
                    'avg_completeness': round(r.avg_completeness, 3) if r.avg_completeness else None,
                    'avg_accuracy': round(r.avg_accuracy, 3) if r.avg_accuracy else None,
                    'avg_consistency': round(r.avg_consistency, 3) if r.avg_consistency else None,
                    'avg_overall': round(r.avg_overall, 3) if r.avg_overall else None,
                    'total_count': r.total_count
                }
                for r in results  # List comprehension - builds list from results
            ]
        finally:
            session.close()
    
    def get_quality_distribution(self, agent_type: Optional[str] = None) -> Dict:
        """
        Get quality distribution (high/medium/low) using raw SQL.
        
        INTERVIEW EXPLANATION:
        This uses raw SQL with CASE statements for conditional logic.
        CASE is like if/else in SQL:
        - CASE WHEN condition THEN value ELSE other_value END
        
        Equivalent SQL:
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN overall_score >= 0.8 THEN 1 ELSE 0 END) as high_quality,
            SUM(CASE WHEN overall_score >= 0.5 AND overall_score < 0.8 THEN 1 ELSE 0 END) as medium_quality,
            SUM(CASE WHEN overall_score < 0.5 THEN 1 ELSE 0 END) as low_quality
        FROM evaluations
        [WHERE agent_type = ?]
        
        Args:
            agent_type: Optional filter by agent type
        
        Returns:
            Dictionary with counts for each quality category
        """
        session = self.db.get_session()
        try:
            # Using raw SQL for complex conditional aggregation
            # Raw SQL gives more control for complex queries
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN overall_score >= 0.8 THEN 1 ELSE 0 END) as high_quality,
                    SUM(CASE WHEN overall_score >= 0.5 AND overall_score < 0.8 THEN 1 ELSE 0 END) as medium_quality,
                    SUM(CASE WHEN overall_score < 0.5 THEN 1 ELSE 0 END) as low_quality
                FROM evaluations
            """
            
            # Add WHERE clause if agent_type specified
            # WARNING: In production, use parameterized queries to prevent SQL injection
            # This is simplified for learning purposes
            if agent_type:
                query += f" WHERE agent_type = '{agent_type}'"
            
            # Execute raw SQL query
            # In SQLAlchemy 2.0+, raw SQL strings must be wrapped in text()
            # session.execute() runs raw SQL
            result = session.execute(text(query)).fetchone()  # fetchone() gets first row
            
            # result is a tuple: (total, high_quality, medium_quality, low_quality)
            return {
                'total': result[0] if result else 0,
                'high_quality': result[1] if result else 0,
                'medium_quality': result[2] if result else 0,
                'low_quality': result[3] if result else 0
            }
        finally:
            session.close()
    
    def get_trend_over_time(self, agent_type: str, days: int = 30) -> List[Dict]:
        """
        Get score trends over time using date grouping.
        
        INTERVIEW EXPLANATION:
        This groups evaluations by date and calculates daily averages.
        Demonstrates time-series analysis:
        - func.date() - Extract date from datetime (SQLite function)
        - Group by date to get daily aggregates
        - Order by date for chronological results
        
        Equivalent SQL:
        SELECT 
            DATE(evaluation_timestamp) as eval_date,
            AVG(overall_score) as avg_score,
            COUNT(id) as count
        FROM evaluations
        WHERE agent_type = ? AND evaluation_timestamp >= cutoff_date
        GROUP BY DATE(evaluation_timestamp)
        ORDER BY DATE(evaluation_timestamp)
        
        Args:
            agent_type: Agent type to analyze
            days: Number of days to look back
        
        Returns:
            List of dictionaries with daily averages
        """
        session = self.db.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # SQLAlchemy query with date grouping
            # func.date() extracts date part from datetime (SQLite specific)
            results = session.query(
                func.date(Evaluation.evaluation_timestamp).label('eval_date'),  # Extract date
                func.avg(Evaluation.overall_score).label('avg_score'),  # Average score per day
                func.count(Evaluation.id).label('count')  # Count of evaluations per day
            ).filter(
                # WHERE agent_type = ? AND evaluation_timestamp >= cutoff_date
                and_(
                    Evaluation.agent_type == agent_type,
                    Evaluation.evaluation_timestamp >= cutoff_date
                )
            ).group_by(
                # GROUP BY DATE(evaluation_timestamp)
                func.date(Evaluation.evaluation_timestamp)
            ).order_by(
                # ORDER BY DATE(evaluation_timestamp) ASC
                func.date(Evaluation.evaluation_timestamp)
            ).all()
            
            # Convert to list of dictionaries
            # Handle both date objects and strings (SQLite DATE() returns string)
            return [
                {
                    'date': (
                        r.eval_date.isoformat() if hasattr(r.eval_date, 'isoformat') 
                        else str(r.eval_date) if r.eval_date 
                        else None
                    ),  # Convert date to ISO string
                    'avg_score': round(r.avg_score, 3) if r.avg_score else None,
                    'count': r.count
                }
                for r in results
            ]
        finally:
            session.close()
    
    def get_top_issues(self, agent_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        Analyze issues_found JSON to find most common issues.
        
        INTERVIEW EXPLANATION:
        This demonstrates JSON processing in Python (since SQLite has limited JSON support).
        Process:
        1. Query all issues_found JSON strings
        2. Parse each JSON string to Python list
        3. Combine all issues into one list
        4. Count frequency of each issue
        5. Return most common issues
        
        In PostgreSQL, you could use JSON functions directly in SQL.
        For SQLite, we process JSON in Python.
        
        Args:
            agent_type: Optional filter by agent type
            limit: Number of top issues to return
        
        Returns:
            List of dictionaries with issue and count, sorted by count (descending)
        """
        session = self.db.get_session()
        try:
            # Query all issues_found fields (they're stored as JSON strings)
            query = session.query(Evaluation.issues_found).filter(
                Evaluation.issues_found.isnot(None)  # Only get non-null values
            )
            if agent_type:
                query = query.filter(Evaluation.agent_type == agent_type)
            
            # Collect all issues from all records
            all_issues = []
            for row in query.all():
                import json
                # Parse JSON string to Python list
                issues = json.loads(row[0]) if row[0] else []
                # Add all issues from this record to our list
                all_issues.extend(issues)
            
            # Count issue frequency using Counter (Python standard library)
            from collections import Counter
            # Counter counts occurrences of each item
            issue_counts = Counter(all_issues)
            
            # Convert to list of dictionaries, sorted by count (most common first)
            # .most_common(limit) returns top N issues
            return [
                {'issue': issue, 'count': count}
                for issue, count in issue_counts.most_common(limit)
            ]
        finally:
            session.close()

