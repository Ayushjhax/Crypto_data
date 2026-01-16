
from sqlalchemy import func, and_, or_, text
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import json
from database.models import Evaluation, EvaluationSummary, PipelineRun, DatabaseManager


class EvaluationQueries:
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_recent_evaluations(self, agent_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        session = self.db.get_session()
        try:
            query = session.query(Evaluation)
            
            if agent_type:
                query = query.filter(Evaluation.agent_type == agent_type)
            
            query = query.order_by(Evaluation.evaluation_timestamp.desc()).limit(limit)
            
            return [e.to_dict() for e in query.all()]
        finally:
            session.close()
    
    def get_avg_scores_by_agent(self, days: int = 7) -> List[Dict]:
        session = self.db.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            results = session.query(
                Evaluation.agent_type,  # Column to group by
                func.avg(Evaluation.completeness_score).label('avg_completeness'),  # AVG() function
                func.avg(Evaluation.accuracy_score).label('avg_accuracy'),
                func.avg(Evaluation.consistency_score).label('avg_consistency'),
                func.avg(Evaluation.overall_score).label('avg_overall'),
                func.count(Evaluation.id).label('total_count')  # COUNT() function
            ).filter(
                Evaluation.evaluation_timestamp >= cutoff_date
            ).group_by(
                Evaluation.agent_type
            ).all()  # Execute query
            
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
        session = self.db.get_session()
        try:
            query_text = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN overall_score >= 0.8 THEN 1 ELSE 0 END) as high_quality,
                    SUM(CASE WHEN overall_score >= 0.5 AND overall_score < 0.8 THEN 1 ELSE 0 END) as medium_quality,
                    SUM(CASE WHEN overall_score < 0.5 THEN 1 ELSE 0 END) as low_quality
                FROM evaluations
            """
            
            if agent_type:
                query_text += " WHERE agent_type = :agent_type"
            
            result = session.execute(text(query_text), {"agent_type": agent_type} if agent_type else {})
            row = result.fetchone()
            
            if row:
                return {
                    'total': row.total,
                    'high_quality': row.high_quality,
                    'medium_quality': row.medium_quality,
                    'low_quality': row.low_quality
                }
            return {'total': 0, 'high_quality': 0, 'medium_quality': 0, 'low_quality': 0}
        finally:
            session.close()
    
    def get_trend_over_time(self, agent_type: str, days: int = 7) -> List[Dict]:
        """Get score trends over time using date grouping.
        
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
            
            results = session.query(
                func.date(Evaluation.evaluation_timestamp).label('eval_date'),
                func.avg(Evaluation.overall_score).label('avg_score'),
                func.count(Evaluation.id).label('count')
            ).filter(
                and_(
                    Evaluation.agent_type == agent_type,
                    Evaluation.evaluation_timestamp >= cutoff_date
                )
            ).group_by(
                func.date(Evaluation.evaluation_timestamp)
            ).order_by(
                func.date(Evaluation.evaluation_timestamp)
            ).all()
            
            return [
                {
                    'date': str(r.eval_date),
                    'avg_score': round(r.avg_score, 3) if r.avg_score else None,
                    'count': r.count
                }
                for r in results
            ]
        finally:
            session.close()
    
    def get_top_issues(self, agent_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Analyze issues_found JSON to find most common issues.
        
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
            query = session.query(Evaluation.issues_found)
            
            if agent_type:
                query = query.filter(Evaluation.agent_type == agent_type)
            
            # Filter out None values
            query = query.filter(Evaluation.issues_found.isnot(None))
            
            rows = query.all()
            
            # Count issues
            issue_counts = {}
            for row in rows:
                if row.issues_found:
                    try:
                        issues = json.loads(row.issues_found)
                        if isinstance(issues, list):
                            for issue in issues:
                                issue_counts[issue] = issue_counts.get(issue, 0) + 1
                    except (json.JSONDecodeError, TypeError):
                        continue
            
            # Sort by count descending and return top N
            sorted_issues = sorted(
                issue_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            return [
                {'issue': issue, 'count': count}
                for issue, count in sorted_issues
            ]
        finally:
            session.close()