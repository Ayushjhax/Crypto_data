"""
CLI commands for generating reports.
"""

import click
from pathlib import Path
from datetime import datetime

from analytics.evaluation_analyzer import EvaluationAnalyzer
from analytics.data_quality_reporter import DataQualityReporter
from cli.utils import print_success, print_error, print_info, print_warning, format_output, save_json_file
from config.settings import QUALITY_REPORTS_DIR
from utils.logger import setup_logger

logger = setup_logger(__name__)


@click.group()
def report():
    """Report generation commands."""
    pass


@report.command()
@click.option('--agent-type', type=click.Choice(['collector', 'cleaner', 'labeler', 'all']), default='all',
              help='Agent type to generate report for')
@click.option('--days', default=7, type=int, help='Number of days to analyze')
@click.option('--output-dir', type=click.Path(path_type=Path), default=None,
              help='Output directory for report')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def evaluation(agent_type, days, output_dir, output_format):
    """Generate evaluation quality report."""
    try:
        print_info(f"Generating evaluation report for {agent_type} (last {days} days)...")
        
        analyzer = EvaluationAnalyzer()
        
        agent_filter = None if agent_type == 'all' else agent_type
        report = analyzer.generate_quality_report(agent_type=agent_filter, days=days)
        
        # Save report if output directory specified
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"evaluation_report_{agent_type}_{timestamp}.json"
            filepath = output_dir / filename
            
            if save_json_file(report, filepath):
                print_success(f"Report saved to {filepath}")
        
        # Display report summary
        print("\n" + "="*60)
        print("EVALUATION QUALITY REPORT")
        print("="*60)
        print(f"\nGenerated: {report.get('generated_at', 'N/A')}")
        print(f"Period: Last {days} days")
        print(f"Agent Type: {agent_type}")
        
        if report.get('summary'):
            summary = report['summary']
            print(f"\nSummary:")
            if 'avg_scores' in summary:
                scores = summary['avg_scores']
                print(f"  Average Completeness: {scores.get('avg_completeness', 'N/A')}")
                print(f"  Average Accuracy: {scores.get('avg_accuracy', 'N/A')}")
                print(f"  Average Consistency: {scores.get('avg_consistency', 'N/A')}")
                print(f"  Average Overall Score: {scores.get('avg_overall_score', 'N/A')}")
        
        if report.get('recommendations'):
            print(f"\nRecommendations:")
            for rec in report['recommendations']:
                print(f"  - {rec}")
        
        if output_format == 'json':
            print("\n" + format_output(report, format=output_format))
        
        analyzer.close()
        
    except Exception as e:
        print_error(f"Report generation failed: {e}")
        logger.error(f"Report generation failed: {e}", exc_info=True)
        raise click.Abort()


@report.command()
@click.option('--output-dir', type=click.Path(path_type=Path), default=None,
              help='Output directory for report (default: data/quality_reports)')
@click.option('--output-format', type=click.Choice(['table', 'json', 'markdown']), default='table',
              help='Output format')
def quality_summary(output_dir, output_format):
    """Generate data quality summary report."""
    try:
        print_info("Generating data quality summary report...")
        
        # This would generate a comprehensive quality report
        # For now, we'll show available quality reports
        output_dir = output_dir or QUALITY_REPORTS_DIR
        
        if output_dir.exists():
            reports = list(output_dir.glob("*.json"))
            if reports:
                print_info(f"Found {len(reports)} quality reports in {output_dir}")
                print("\nRecent Reports:")
                for report_file in sorted(reports, key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
                    mtime = datetime.fromtimestamp(report_file.stat().st_mtime)
                    print(f"  - {report_file.name} ({mtime.strftime('%Y-%m-%d %H:%M:%S')})")
            else:
                print_warning(f"No quality reports found in {output_dir}")
        else:
            print_warning(f"Output directory does not exist: {output_dir}")
        
    except Exception as e:
        print_error(f"Report generation failed: {e}")
        logger.error(f"Report generation failed: {e}", exc_info=True)
        raise click.Abort()

