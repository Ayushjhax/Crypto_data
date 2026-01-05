"""
CLI commands for data quality checks and reports.
"""

import click
from pathlib import Path
import json

from analytics.data_quality_reporter import DataQualityReporter
from core.data_standards import DataDictionary
from config.settings import RAW_DATA_DIR, CLEANED_DATA_DIR, LABELED_DATA_DIR, QUALITY_REPORTS_DIR
from cli.utils import print_success, print_error, print_info, print_warning, format_output, load_json_file
from utils.logger import setup_logger

logger = setup_logger(__name__)


@click.group()
def quality():
    """Data quality check commands."""
    pass


@quality.command()
@click.argument('filepath', type=click.Path(exists=True, path_type=Path))
@click.option('--report-type', type=click.Choice(['full', 'summary', 'quick']), default='full',
              help='Type of quality report to generate')
@click.option('--save/--no-save', default=True, help='Save report to file')
@click.option('--output-format', type=click.Choice(['table', 'json', 'markdown']), default='table',
              help='Output format')
def check(filepath, report_type, save, output_format):
    """Check data quality for a specific file."""
    try:
        print_info(f"Checking data quality for {filepath.name}...")
        
        # Load data
        data = load_json_file(filepath)
        if not data:
            print_error(f"Failed to load data from {filepath}")
            raise click.Abort()
        
        # Generate quality report
        reporter = DataQualityReporter()
        report = reporter.generate_report(data, report_type=report_type)
        
        # Save report if requested
        if save:
            report_path = reporter.save_report(report, format='json' if output_format == 'json' else 'markdown')
            print_success(f"Quality report saved to {report_path}")
        
        # Display report
        if output_format == 'table':
            print("\n" + "="*60)
            print("DATA QUALITY REPORT")
            print("="*60)
            print(f"\nOverall Quality Score: {report['quality_score']['overall_score']}/100 ({report['quality_score']['grade']})")
            print(f"\nCompleteness: {report['completeness']['required_completeness_percentage']}% ({report['completeness']['grade']})")
            print(f"Validity: {report['validity']['validity_percentage']}% ({report['validity']['grade']})")
            print(f"Consistency: {report['consistency']['consistency_percentage']}% ({report['consistency']['grade']})")
            
            if report['completeness']['missing_required_fields']:
                print(f"\nMissing Required Fields: {', '.join(report['completeness']['missing_required_fields'])}")
            
            if report['validity']['total_errors'] > 0:
                print(f"\nValidation Errors: {report['validity']['total_errors']}")
            
            if report['consistency']['consistency_issues']:
                print(f"\nConsistency Issues:")
                for issue in report['consistency']['consistency_issues']:
                    print(f"  - {issue}")
            
            if report['recommendations']:
                print(f"\nRecommendations:")
                for rec in report['recommendations']:
                    print(f"  - {rec}")
        else:
            print(format_output(report, format=output_format))
        
    except Exception as e:
        print_error(f"Quality check failed: {e}")
        logger.error(f"Quality check failed: {e}", exc_info=True)
        raise click.Abort()


@quality.command()
@click.option('--data-dir', type=click.Choice(['raw', 'cleaned', 'labeled']), default='cleaned',
              help='Directory to check')
@click.option('--save/--no-save', default=True, help='Save reports to files')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def batch(data_dir, save, output_format):
    """Check quality for all files in a directory."""
    try:
        # Select directory
        if data_dir == 'raw':
            data_dir_path = RAW_DATA_DIR
        elif data_dir == 'cleaned':
            data_dir_path = CLEANED_DATA_DIR
        else:
            data_dir_path = LABELED_DATA_DIR
        
        # Get all JSON files
        files = list(data_dir_path.glob("*.json"))
        files = [f for f in files if not f.name.startswith("all_coins")]
        
        if not files:
            print_warning(f"No data files found in {data_dir} directory")
            return
        
        print_info(f"Checking quality for {len(files)} files in {data_dir} directory...")
        
        reporter = DataQualityReporter()
        all_data = []
        
        for filepath in files:
            data = load_json_file(filepath)
            if data:
                all_data.append(data)
        
        if all_data:
            # Generate batch report
            batch_report = reporter.generate_batch_report(all_data)
            
            # Save if requested
            if save:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_path = QUALITY_REPORTS_DIR / f"batch_quality_report_{data_dir}_{timestamp}.json"
                report_path.parent.mkdir(parents=True, exist_ok=True)
                with open(report_path, 'w') as f:
                    json.dump(batch_report, f, indent=2, default=str)
                print_success(f"Batch quality report saved to {report_path}")
            
            # Display summary
            print("\n" + "="*60)
            print("BATCH QUALITY REPORT")
            print("="*60)
            print(f"\nTotal Records: {batch_report['report_metadata']['total_records']}")
            print(f"\nAverage Scores:")
            print(f"  Overall: {batch_report['aggregate_scores']['overall_average']}/100")
            print(f"  Completeness: {batch_report['aggregate_scores']['completeness_average']}/100")
            print(f"  Validity: {batch_report['aggregate_scores']['validity_average']}/100")
            print(f"  Consistency: {batch_report['aggregate_scores']['consistency_average']}/100")
            
            if batch_report['common_issues']:
                print(f"\nCommon Issues:")
                for issue_info in batch_report['common_issues']:
                    print(f"  - {issue_info['issue']} (count: {issue_info['count']})")
        else:
            print_error("No valid data files found")
        
    except Exception as e:
        print_error(f"Batch quality check failed: {e}")
        logger.error(f"Batch quality check failed: {e}", exc_info=True)
        raise click.Abort()


@quality.command()
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def standards(output_format):
    """Show data standards and dictionary information."""
    try:
        dictionary = DataDictionary()
        
        print("Data Standards & Dictionary")
        print("="*60)
        print(f"Version: {dictionary.version}")
        print(f"Last Updated: {dictionary.last_updated}")
        print(f"Total Fields: {len(dictionary.fields)}")
        
        if output_format == 'json':
            fields_dict = {name: field.to_dict() for name, field in dictionary.fields.items()}
            print(format_output({
                'version': dictionary.version,
                'last_updated': dictionary.last_updated,
                'fields': fields_dict
            }, format=output_format))
        else:
            print("\nField Definitions:")
            for name, field in dictionary.fields.items():
                print(f"\n  {name}:")
                print(f"    Type: {field.data_type.value}")
                print(f"    Required: {field.required}")
                print(f"    Description: {field.description}")
                if field.example:
                    print(f"    Example: {field.example}")
        
    except Exception as e:
        print_error(f"Error showing standards: {e}")
        logger.error(f"Error showing standards: {e}", exc_info=True)
        raise click.Abort()

