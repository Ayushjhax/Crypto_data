"""
Data quality report generator.

INTERVIEW EXPLANATION:
This module generates comprehensive data quality reports that:
1. Analyze data against standards (data dictionary)
2. Calculate quality metrics
3. Identify issues and trends
4. Provide actionable recommendations

Reports are essential for:
- Monitoring data quality over time
- Identifying systematic issues
- Demonstrating data governance
- Meeting compliance requirements
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import json

from core.data_standards import DataDictionary
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DataQualityReporter:
    """
    Generates comprehensive data quality reports.
    
    INTERVIEW EXPLANATION:
    This class combines:
    - Data dictionary (standards)
    - Quality metrics calculation
    - Report generation
    - Trend analysis
    """
    
    def __init__(self, dictionary: Optional[DataDictionary] = None):
        """
        Initialize reporter.
        
        Args:
            dictionary: Data dictionary instance (creates new one if None)
        """
        self.dictionary = dictionary or DataDictionary()
        self.report_history = []
    
    def generate_report(
        self,
        data: Dict[str, Any],
        report_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive data quality report.
        
        Args:
            data: Data record to analyze
            report_type: "full", "summary", or "quick"
        
        Returns:
            Complete quality report dictionary
        """
        logger.info(f"Generating {report_type} quality report for {data.get('symbol', 'unknown')}")
        
        # Validate data against dictionary
        validation_errors = self.dictionary.validate_data(data)
        
        # Calculate metrics
        completeness = self._analyze_completeness(data)
        validity = self._analyze_validity(data, validation_errors)
        consistency = self._analyze_consistency(data)
        quality_score = self._calculate_quality_score(completeness, validity, consistency)
        
        # Build report
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "data_source": data.get("symbol", "unknown"),
                "report_type": report_type,
                "report_version": "1.0",
                "dictionary_version": self.dictionary.version
            },
            "quality_score": quality_score,
            "completeness": completeness,
            "validity": validity,
            "consistency": consistency,
            "recommendations": self._generate_recommendations(
                completeness, validity, consistency, validation_errors
            )
        }
        
        # Add detailed analysis for full reports
        if report_type == "full":
            report["field_analysis"] = self._analyze_fields(data)
            report["validation_details"] = validation_errors
        
        self.report_history.append(report)
        return report
    
    def _analyze_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data completeness."""
        total_fields = len(self.dictionary.fields)
        present_fields = sum(
            1 for field_name in self.dictionary.fields
            if field_name in data and data[field_name] is not None
        )
        
        required_fields = [
            name for name, field in self.dictionary.fields.items()
            if field.required
        ]
        present_required = sum(
            1 for name in required_fields
            if name in data and data[name] is not None
        )
        
        missing_fields = [
            name for name in self.dictionary.fields
            if name not in data or data[name] is None
        ]
        missing_required = [
            name for name in required_fields
            if name not in data or data[name] is None
        ]
        
        completeness_pct = (present_fields / total_fields * 100) if total_fields > 0 else 0
        required_completeness_pct = (
            (present_required / len(required_fields) * 100)
            if required_fields else 100
        )
        
        return {
            "total_fields": total_fields,
            "present_fields": present_fields,
            "missing_fields": missing_fields,
            "completeness_percentage": round(completeness_pct, 2),
            "required_fields_count": len(required_fields),
            "present_required_count": present_required,
            "missing_required_fields": missing_required,
            "required_completeness_percentage": round(required_completeness_pct, 2),
            "grade": self._grade_score(required_completeness_pct)
        }
    
    def _analyze_validity(
        self,
        data: Dict[str, Any],
        validation_errors: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Analyze data validity against standards."""
        total_errors = sum(len(errors) for errors in validation_errors.values())
        total_fields = len(self.dictionary.fields)
        
        # Calculate validity percentage
        # Each error reduces score, but we weight by field importance
        error_weight = total_errors / total_fields if total_fields > 0 else 0
        validity_pct = max(0, 100 - (error_weight * 100))
        
        return {
            "total_errors": total_errors,
            "error_breakdown": {
                "missing_required": len(validation_errors.get("missing_required", [])),
                "type_errors": len(validation_errors.get("type_errors", [])),
                "validation_errors": len(validation_errors.get("validation_errors", [])),
                "unknown_fields": len(validation_errors.get("unknown_fields", []))
            },
            "validity_percentage": round(validity_pct, 2),
            "grade": self._grade_score(validity_pct),
            "errors": validation_errors
        }
    
    def _analyze_consistency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data consistency and logical relationships."""
        issues = []
        
        # Check price relationships
        if all(k in data for k in ["price", "lowest_24h", "highest_24h"]):
            price = data.get("price")
            lowest = data.get("lowest_24h")
            highest = data.get("highest_24h")
            
            if price and lowest and highest:
                if lowest > highest:
                    issues.append("lowest_24h > highest_24h (logical inconsistency)")
                elif price < lowest * 0.9:
                    issues.append("Price significantly below 24h low (possible outlier)")
                elif price > highest * 1.1:
                    issues.append("Price significantly above 24h high (possible outlier)")
        
        # Check label consistency
        if "price_movement" in data and "price_change_24h" in data:
            movement = data.get("price_movement")
            change = data.get("price_change_24h")
            
            if change is not None and movement:
                # Basic consistency check
                if change > 5 and movement not in ["strong_up", "up"]:
                    issues.append("price_movement label may not match price_change_24h value")
                elif change < -5 and movement not in ["strong_down", "down"]:
                    issues.append("price_movement label may not match price_change_24h value")
        
        # Check for unusual values
        if "price_change_24h" in data and data["price_change_24h"]:
            change = abs(data["price_change_24h"])
            if change > 50:
                issues.append(f"Unusual price change detected: {data['price_change_24h']}%")
        
        consistency_pct = 100 if not issues else max(0, 100 - (len(issues) * 20))
        
        return {
            "consistency_issues": issues,
            "issues_count": len(issues),
            "is_consistent": len(issues) == 0,
            "consistency_percentage": round(consistency_pct, 2),
            "grade": self._grade_score(consistency_pct)
        }
    
    def _analyze_fields(self, data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Detailed analysis of each field."""
        field_analysis = {}
        
        for field_name, field_def in self.dictionary.fields.items():
            value = data.get(field_name)
            
            analysis = {
                "present": field_name in data and value is not None,
                "required": field_def.required,
                "value": value,
                "type": type(value).__name__ if value is not None else None,
                "expected_type": field_def.data_type.value,
                "validation_errors": []
            }
            
            # Validate this field
            if field_name in data:
                errors = self.dictionary.validate_field(field_name, value)
                analysis["validation_errors"] = errors
                analysis["is_valid"] = len(errors) == 0
            
            field_analysis[field_name] = analysis
        
        return field_analysis
    
    def _calculate_quality_score(
        self,
        completeness: Dict[str, Any],
        validity: Dict[str, Any],
        consistency: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall quality score."""
        # Weighted average
        score = (
            completeness["required_completeness_percentage"] * 0.4 +
            validity["validity_percentage"] * 0.4 +
            consistency["consistency_percentage"] * 0.2
        )
        
        return {
            "overall_score": round(score, 2),
            "grade": self._grade_score(score),
            "components": {
                "completeness": completeness["required_completeness_percentage"],
                "validity": validity["validity_percentage"],
                "consistency": consistency["consistency_percentage"]
            }
        }
    
    def _grade_score(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _generate_recommendations(
        self,
        completeness: Dict[str, Any],
        validity: Dict[str, Any],
        consistency: Dict[str, Any],
        validation_errors: Dict[str, List[str]]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Completeness recommendations
        if completeness["required_completeness_percentage"] < 100:
            missing = completeness["missing_required_fields"]
            recommendations.append(
                f"Add missing required fields: {', '.join(missing)}"
            )
        
        # Validity recommendations
        if validity["total_errors"] > 0:
            if validation_errors.get("type_errors"):
                recommendations.append(
                    "Fix data type mismatches - ensure values match expected types"
                )
            if validation_errors.get("validation_errors"):
                recommendations.append(
                    "Review validation rule violations - values may be out of acceptable ranges"
                )
        
        # Consistency recommendations
        if consistency["issues_count"] > 0:
            recommendations.append(
                f"Address {consistency['issues_count']} consistency issue(s) - "
                "check logical relationships between fields"
            )
        
        # Positive feedback
        if (completeness["required_completeness_percentage"] == 100 and
            validity["total_errors"] == 0 and
            consistency["issues_count"] == 0):
            recommendations.append("Data quality is excellent - maintain current standards")
        
        return recommendations
    
    def save_report(
        self,
        report: Dict[str, Any],
        output_path: Optional[Path] = None,
        format: str = "json"
    ) -> Path:
        """
        Save report to file.
        
        Args:
            report: Report dictionary to save
            output_path: Optional custom path
            format: "json" or "markdown"
        
        Returns:
            Path to saved file
        """
        from config.settings import QUALITY_REPORTS_DIR
        
        if not output_path:
            symbol = report["report_metadata"]["data_source"]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{symbol}_quality_report_{timestamp}.{format}"
            output_path = QUALITY_REPORTS_DIR / filename
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)
        elif format == "markdown":
            markdown = self._report_to_markdown(report)
            with open(output_path, "w") as f:
                f.write(markdown)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Saved quality report to {output_path}")
        return output_path
    
    def _report_to_markdown(self, report: Dict[str, Any]) -> str:
        """Convert report to Markdown format."""
        lines = [
            "# Data Quality Report",
            "",
            f"**Generated:** {report['report_metadata']['generated_at']}",
            f"**Data Source:** {report['report_metadata']['data_source']}",
            f"**Report Type:** {report['report_metadata']['report_type']}",
            "",
            "## Quality Score",
            "",
            f"**Overall Score:** {report['quality_score']['overall_score']}/100 ({report['quality_score']['grade']})",
            "",
            "### Component Scores",
            "",
            f"- **Completeness:** {report['quality_score']['components']['completeness']}/100",
            f"- **Validity:** {report['quality_score']['components']['validity']}/100",
            f"- **Consistency:** {report['quality_score']['components']['consistency']}/100",
            "",
            "## Completeness Analysis",
            "",
            f"- **Total Fields:** {report['completeness']['total_fields']}",
            f"- **Present Fields:** {report['completeness']['present_fields']}",
            f"- **Completeness:** {report['completeness']['completeness_percentage']}% ({report['completeness']['grade']})",
            f"- **Required Fields Complete:** {report['completeness']['required_completeness_percentage']}%",
            ""
        ]
        
        if report['completeness']['missing_required_fields']:
            lines.extend([
                "### Missing Required Fields",
                ""
            ])
            for field in report['completeness']['missing_required_fields']:
                lines.append(f"- {field}")
            lines.append("")
        
        lines.extend([
            "## Validity Analysis",
            "",
            f"- **Total Errors:** {report['validity']['total_errors']}",
            f"- **Validity Score:** {report['validity']['validity_percentage']}% ({report['validity']['grade']})",
            ""
        ])
        
        if report['validity']['total_errors'] > 0:
            lines.append("### Error Breakdown")
            lines.append("")
            for error_type, count in report['validity']['error_breakdown'].items():
                if count > 0:
                    lines.append(f"- **{error_type.replace('_', ' ').title()}:** {count}")
            lines.append("")
        
        lines.extend([
            "## Consistency Analysis",
            "",
            f"- **Issues Found:** {report['consistency']['issues_count']}",
            f"- **Consistency Score:** {report['consistency']['consistency_percentage']}% ({report['consistency']['grade']})",
            ""
        ])
        
        if report['consistency']['consistency_issues']:
            lines.append("### Consistency Issues")
            lines.append("")
            for issue in report['consistency']['consistency_issues']:
                lines.append(f"- {issue}")
            lines.append("")
        
        lines.extend([
            "## Recommendations",
            ""
        ])
        
        for rec in report['recommendations']:
            lines.append(f"- {rec}")
        
        lines.append("")
        
        return "\n".join(lines)
    
    def generate_batch_report(
        self,
        data_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate aggregate report for multiple data records.
        
        Args:
            data_list: List of data dictionaries
        
        Returns:
            Aggregate quality report
        """
        reports = [self.generate_report(data, report_type="summary") for data in data_list]
        
        # Calculate averages
        avg_scores = {
            "completeness": sum(r["completeness"]["required_completeness_percentage"] for r in reports) / len(reports),
            "validity": sum(r["validity"]["validity_percentage"] for r in reports) / len(reports),
            "consistency": sum(r["consistency"]["consistency_percentage"] for r in reports) / len(reports)
        }
        
        overall_avg = (
            avg_scores["completeness"] * 0.4 +
            avg_scores["validity"] * 0.4 +
            avg_scores["consistency"] * 0.2
        )
        
        # Collect common issues
        all_issues = []
        for report in reports:
            all_issues.extend(report["consistency"]["consistency_issues"])
        
        from collections import Counter
        common_issues = Counter(all_issues).most_common(5)
        
        return {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_type": "batch",
                "total_records": len(data_list),
                "report_version": "1.0"
            },
            "aggregate_scores": {
                "overall_average": round(overall_avg, 2),
                "completeness_average": round(avg_scores["completeness"], 2),
                "validity_average": round(avg_scores["validity"], 2),
                "consistency_average": round(avg_scores["consistency"], 2)
            },
            "individual_reports": reports,
            "common_issues": [{"issue": issue, "count": count} for issue, count in common_issues]
        }

