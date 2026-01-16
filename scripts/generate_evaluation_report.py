
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from analytics.evaluation_analyzer import EvaluationAnalyzer
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    analyzer = EvaluationAnalyzer()
    
    try:
        report = analyzer.generate_quality_report(days=30)
        
        output_dir = Path("data/quality_reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"quality_report_{timestamp}.json"
        
        analyzer.export_report_json(report, str(report_path))
        
        print("=" * 60)
        print("EVALUATION REPORT SUMMARY")
        print("=" * 60)
        
        print(f"\nAverage Scores (last 30 days):")
        avg_scores = report['summary'].get('average_scores', [])
        if avg_scores:
            for score_data in avg_scores:
                agent = score_data['agent_type']
                overall = score_data.get('avg_overall', 'N/A')
                print(f"  {agent:12} Overall Score: {overall}")
        else:
            print("  No evaluation data found")
        
        print(f"\nQuality Distribution:")
        dist = report['summary'].get('quality_distribution', {})
        total = dist.get('total', 0)
        if total > 0:
            print(f"  Total Evaluations: {total}")
            print(f"  High Quality (>0.8):   {dist.get('high_quality', 0):4} "
                  f"({(dist.get('high_quality', 0)/total*100):5.1f}%)")
            print(f"  Medium Quality (0.5-0.8): {dist.get('medium_quality', 0):4} "
                  f"({(dist.get('medium_quality', 0)/total*100):5.1f}%)")
            print(f"  Low Quality (<0.5):    {dist.get('low_quality', 0):4} "
                  f"({(dist.get('low_quality', 0)/total*100):5.1f}%)")
        else:
            print("  No evaluation data found")
        
        print(f"\nTop Recommendations:")
        recommendations = report.get('recommendations', [])
        if recommendations:
            for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
                print(f"  {i}. {rec}")
        else:
            print("  No recommendations")
        
        print(f"\nFull report saved to: {report_path}")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1
    finally:
        analyzer.close()
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

