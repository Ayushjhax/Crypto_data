
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from database.models import DatabaseManager
from database.queries import EvaluationQueries
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EvaluationAnalyzer:
    
    def __init__(self, db_path: str = "data/evaluations.db"):
        self.db_manager = DatabaseManager(db_path)
        self.queries = EvaluationQueries(self.db_manager)
    
    def generate_quality_report(
        self, 
        agent_type: Optional[str] = None, 
        days: int = 7
    ) -> Dict[str, Any]:
        logger.info(f"Generating quality report for {agent_type or 'all agents'} (last {days} days)")
        
        report = {
            'generated_at': datetime.now().isoformat(),  # When report was generated
            'period_days': days,
            'agent_type': agent_type,
            'summary': {},      # Summary statistics
            'trends': {},       # Trends over time
            'issues': {},       # Issue analysis
            'recommendations': []  # Actionable recommendations
        }
        
        avg_scores = self.queries.get_avg_scores_by_agent(days)
        
        if agent_type:
            avg_scores = [s for s in avg_scores if s['agent_type'] == agent_type]
        
        report['summary']['average_scores'] = avg_scores
        
        distribution = self.queries.get_quality_distribution(agent_type)
        report['summary']['quality_distribution'] = distribution
        
        total = distribution['total']
        if total > 0:
            report['summary']['quality_percentages'] = {
                'high_quality': round((distribution['high_quality'] / total) * 100, 2),
                'medium_quality': round((distribution['medium_quality'] / total) * 100, 2),
                'low_quality': round((distribution['low_quality'] / total) * 100, 2)
            }
        
        if agent_type:
            trends = self.queries.get_trend_over_time(agent_type, days)
            report['trends'] = trends
        else:
            agent_types = ['collector', 'cleaner', 'labeler']
            report['trends'] = {
                agent: self.queries.get_trend_over_time(agent, days)
                for agent in agent_types
            }
        
        top_issues = self.queries.get_top_issues(agent_type, limit=10)
        report['issues']['top_issues'] = top_issues
        
        report['recommendations'] = self._generate_recommendations_from_report(report)
        
        return report
    
    def _generate_recommendations_from_report(self, report: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        dist = report['summary'].get('quality_distribution', {})
        total = dist.get('total', 0)
        
        if total > 0:
            low_quality_pct = (dist.get('low_quality', 0) / total) * 100
            
            if low_quality_pct > 20:
                recommendations.append(
                    f"High percentage ({low_quality_pct:.1f}%) of low quality data. "
                    "Review data collection and cleaning processes."
                )
        
        avg_scores = report['summary'].get('average_scores', [])
        for score_data in avg_scores:
            avg_overall = score_data.get('avg_overall', 1.0)
            if avg_overall < 0.7:
                recommendations.append(
                    f"{score_data['agent_type']} agent has low average score "
                    f"({avg_overall:.3f}). Consider improving validation."
                )
        
        top_issues = report['issues'].get('top_issues', [])
        if top_issues:
            most_common = top_issues[0]
            recommendations.append(
                f"Most common issue: '{most_common['issue']}' "
                f"(occurs {most_common['count']} times). "
                "Address this to improve overall quality."
            )
        
        if not recommendations:
            recommendations.append("Data quality is good. Continue monitoring.")
        
        return recommendations
    
    def export_report_json(self, report: Dict[str, Any], filepath: str):
        import json
        from pathlib import Path
        
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Exported report to {filepath}")
    
    def close(self):
        self.db_manager.close()

