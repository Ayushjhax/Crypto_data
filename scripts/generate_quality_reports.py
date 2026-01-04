"""
Script to generate data quality reports for all collected data.

INTERVIEW EXPLANATION:
This script demonstrates:
- Batch processing of data files
- Automated report generation
- Integration of data standards and quality reporting

Usage:
    python scripts/generate_quality_reports.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
from core.data_standards import DataDictionary
from analytics.data_quality_reporter import DataQualityReporter
from config.settings import LABELED_DATA_DIR, QUALITY_REPORTS_DIR
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Generate quality reports for all labeled data files."""
    logger.info("=" * 60)
    logger.info("DonutAI - Data Quality Report Generator")
    logger.info("=" * 60)
    
    # Initialize components
    dictionary = DataDictionary()
    reporter = DataQualityReporter(dictionary)
    
    # Find all labeled data files
    labeled_files = list(LABELED_DATA_DIR.glob("*.json"))
    
    if not labeled_files:
        logger.warning("No labeled data files found")
        print("\n⚠️  No labeled data files found in data/labeled/")
        print("   Run the main pipeline first to generate labeled data.")
        return
    
    logger.info(f"Found {len(labeled_files)} labeled data files")
    print(f"\n📊 Found {len(labeled_files)} labeled data files")
    
    reports_generated = 0
    all_data = []
    
    for file_path in labeled_files:
        try:
            # Load data
            with open(file_path, "r") as f:
                data = json.load(f)
            
            # Handle both single records and lists
            if isinstance(data, list):
                records = data
            else:
                records = [data]
            
            # Generate report for each record
            for record in records:
                all_data.append(record)
                report = reporter.generate_report(record, report_type="full")
                
                # Save report
                reporter.save_report(report, format="json")
                reporter.save_report(report, format="markdown")
                
                reports_generated += 1
                
                symbol = record.get('symbol', 'unknown')
                score = report['quality_score']['overall_score']
                grade = report['quality_score']['grade']
                
                logger.info(
                    f"Generated report for {symbol} - "
                    f"Score: {score}/100 ({grade})"
                )
                print(f"  ✅ {symbol}: {score}/100 ({grade})")
        
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            print(f"  ❌ Error processing {file_path.name}: {e}")
    
    # Generate batch summary report
    if reports_generated > 0:
        logger.info("\nGenerating batch summary report...")
        print("\n📈 Generating batch summary report...")
        
        batch_report = reporter.generate_batch_report(all_data)
        
        # Save batch report
        timestamp = batch_report['report_metadata']['generated_at'].replace(':', '-').split('.')[0]
        batch_json_path = QUALITY_REPORTS_DIR / f"batch_summary_{timestamp}.json"
        batch_md_path = QUALITY_REPORTS_DIR / f"batch_summary_{timestamp}.md"
        
        with open(batch_json_path, "w") as f:
            json.dump(batch_report, f, indent=2)
        
        # Create markdown summary
        md_lines = [
            "# Batch Quality Summary Report",
            "",
            f"**Generated:** {batch_report['report_metadata']['generated_at']}",
            f"**Total Records:** {batch_report['report_metadata']['total_records']}",
            "",
            "## Aggregate Scores",
            "",
            f"- **Overall Average:** {batch_report['aggregate_scores']['overall_average']}/100",
            f"- **Completeness Average:** {batch_report['aggregate_scores']['completeness_average']}/100",
            f"- **Validity Average:** {batch_report['aggregate_scores']['validity_average']}/100",
            f"- **Consistency Average:** {batch_report['aggregate_scores']['consistency_average']}/100",
            ""
        ]
        
        if batch_report['common_issues']:
            md_lines.extend([
                "## Common Issues",
                ""
            ])
            for item in batch_report['common_issues']:
                md_lines.append(f"- **{item['issue']}:** {item['count']} occurrences")
            md_lines.append("")
        
        with open(batch_md_path, "w") as f:
            f.write("\n".join(md_lines))
        
        logger.info(f"Saved batch report to {batch_json_path}")
        print(f"  ✅ Batch summary saved")
        
        # Export data dictionary
        logger.info("Exporting data dictionary...")
        print("\n📚 Exporting data dictionary...")
        
        dict_path = QUALITY_REPORTS_DIR / "data_dictionary.md"
        with open(dict_path, "w") as f:
            f.write(dictionary.export_markdown())
        
        logger.info(f"Data dictionary exported to: {dict_path}")
        print(f"  ✅ Data dictionary saved")
        
        # Summary
        print("\n" + "=" * 60)
        print("QUALITY REPORTS GENERATED")
        print("=" * 60)
        print(f"\n✅ Generated {reports_generated} individual reports")
        print(f"✅ Generated 1 batch summary report")
        print(f"✅ Exported data dictionary")
        print(f"\n📁 Reports saved to: {QUALITY_REPORTS_DIR}")
        print("\n" + "=" * 60)
    else:
        print("\n⚠️  No reports generated")


if __name__ == "__main__":
    main()

