
import click
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cli.commands import collect, clean, label, evaluate, quality, analytics, anomaly, report, standards
from cli.utils import print_info, print_success, print_error, print_warning
from utils.logger import setup_logger

logger = setup_logger(__name__)


@click.group()
@click.version_option(version='1.0.0')
def cli():
    pass


cli.add_command(collect.collect, name='collect')
cli.add_command(clean.clean, name='clean')
cli.add_command(label.label, name='label')
cli.add_command(evaluate.evaluate, name='evaluate')
cli.add_command(quality.quality, name='quality')
cli.add_command(analytics.analytics, name='analytics')
cli.add_command(anomaly.anomaly, name='anomaly')
cli.add_command(report.report, name='report')
cli.add_command(standards.standards, name='standards')


@cli.command()
def pipeline():
    try:
        print_info("Starting complete pipeline...")
        
        from main import main as run_pipeline
        
        exit_code = run_pipeline()
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print_info("Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        print(f"❌ Pipeline failed: {e}")
        sys.exit(1)


@cli.command(name='run-all')
@click.option('--skip-analytics', is_flag=True, help='Skip analytics and report generation')
@click.option('--skip-reports', is_flag=True, help='Skip report generation')
@click.option('--analytics-days', default=30, help='Number of days for analytics (default: 30)')
def run_all(skip_analytics, skip_reports, analytics_days):
    try:
        print("\n" + "="*60)
        print("🚀 DONUTAI - RUNNING EVERYTHING")
        print("="*60 + "\n")
        
        print("📊 STEP 1: Running Complete Pipeline...")
        print("-" * 60)
        try:
            from main import main as run_pipeline
            exit_code = run_pipeline()
            if exit_code != 0:
                print_warning(f"Pipeline completed with exit code {exit_code}")
            else:
                print_success("Pipeline completed successfully!")
        except Exception as e:
            print_error(f"Pipeline failed: {e}")
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            if not skip_analytics:  # Continue if analytics is enabled
                print_warning("Continuing with analytics despite pipeline issues...")
            else:
                raise
        
        print("\n")
        
        if not skip_analytics:
            print("📈 STEP 2: Generating Analytics Summary...")
            print("-" * 60)
            try:
                from analytics.metrics_calculator import MetricsCalculator
                calculator = MetricsCalculator()
                summary = calculator.get_summary(days=analytics_days)
                
                print_success(f"Analytics summary generated for last {analytics_days} days")
                print(f"\n  DAU (Current): {summary['dau']['current']}")
                print(f"  Total Sessions: {summary['feature_usage']['total_sessions']}")
                print(f"  Completion Rate: {summary['feature_usage']['completion_rate']:.2f}%")
                
                calculator.close()
            except Exception as e:
                print_warning(f"Analytics generation failed: {e}")
                logger.error(f"Analytics failed: {e}", exc_info=True)
        
        print("\n")
        
        if not skip_reports:
            print("📄 STEP 3: Generating Reports...")
            print("-" * 60)
            try:
                from analytics.evaluation_analyzer import EvaluationAnalyzer
                analyzer = EvaluationAnalyzer()
                
                report = analyzer.generate_quality_report(days=7)
                print_success("Evaluation quality report generated")
                
                analyzer.close()
            except Exception as e:
                print_warning(f"Report generation failed: {e}")
                logger.error(f"Report generation failed: {e}", exc_info=True)
        
        print("\n")
        
        print("📋 STEP 4: Final System Status...")
        print("-" * 60)
        try:
            from config.settings import RAW_DATA_DIR, CLEANED_DATA_DIR, LABELED_DATA_DIR
            
            raw_files = len(list(RAW_DATA_DIR.glob("*.json"))) if RAW_DATA_DIR.exists() else 0
            cleaned_files = len(list(CLEANED_DATA_DIR.glob("*.json"))) if CLEANED_DATA_DIR.exists() else 0
            labeled_files = len(list(LABELED_DATA_DIR.glob("*.json"))) if LABELED_DATA_DIR.exists() else 0
            
            print(f"\nData Files:")
            print(f"  ✅ Raw: {raw_files} files")
            print(f"  ✅ Cleaned: {cleaned_files} files")
            print(f"  ✅ Labeled: {labeled_files} files")
            
            eval_db = Path("data/evaluations.db")
            if eval_db.exists():
                size_mb = eval_db.stat().st_size / (1024 * 1024)
                print(f"\nDatabases:")
                print(f"  ✅ Evaluations DB: {size_mb:.2f} MB")
            else:
                print(f"\nDatabases:")
                print(f"  ⚠️  Evaluations DB: Not found")
            
            print("\n" + "="*60)
            print_success("🎉 ALL OPERATIONS COMPLETED!")
            print("="*60 + "\n")
            
        except Exception as e:
            print_warning(f"Status check failed: {e}")
            logger.error(f"Status check failed: {e}", exc_info=True)
        
    except KeyboardInterrupt:
        print_info("\n⚠️  Operation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Run all failed: {e}", exc_info=True)
        print_error(f"Run all failed: {e}")
        sys.exit(1)


@cli.command()
def status():
    try:
        from config.settings import RAW_DATA_DIR, CLEANED_DATA_DIR, LABELED_DATA_DIR
        from pathlib import Path
        
        print("System Status")
        print("="*60)
        
        raw_files = len(list(RAW_DATA_DIR.glob("*.json"))) if RAW_DATA_DIR.exists() else 0
        cleaned_files = len(list(CLEANED_DATA_DIR.glob("*.json"))) if CLEANED_DATA_DIR.exists() else 0
        labeled_files = len(list(LABELED_DATA_DIR.glob("*.json"))) if LABELED_DATA_DIR.exists() else 0
        
        print(f"\nData Files:")
        print(f"  Raw: {raw_files} files")
        print(f"  Cleaned: {cleaned_files} files")
        print(f"  Labeled: {labeled_files} files")
        
        eval_db = Path("data/evaluations.db")
        if eval_db.exists():
            size_mb = eval_db.stat().st_size / (1024 * 1024)
            print(f"\nDatabases:")
            print(f"  Evaluations DB: {size_mb:.2f} MB")
        else:
            print(f"\nDatabases:")
            print(f"  Evaluations DB: Not found")
        
        print("\n✅ System is operational")
        
    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        print(f"❌ Error getting status: {e}")
        sys.exit(1)


if __name__ == '__main__':
    cli()

