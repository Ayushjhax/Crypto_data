# Data Standards & Quality Reporting Guide

## Overview

This guide explains how to use the new **Data Standards** and **Data Quality Reporting** features in DonutAI. These features help you:

1. **Define Data Standards**: Create a data dictionary that documents all fields
2. **Validate Data**: Automatically check data against standards
3. **Generate Quality Reports**: Create comprehensive reports showing data quality metrics

## Quick Start

### 1. Generate Quality Reports

After running the main pipeline, generate quality reports for all your labeled data:

```bash
python scripts/generate_quality_reports.py
```

This will:
- Analyze all labeled data files
- Generate individual quality reports (JSON and Markdown)
- Create a batch summary report
- Export the data dictionary as Markdown

Reports are saved to: `data/quality_reports/`

### 2. Use in Your Code

```python
from core.data_standards import DataDictionary
from analytics.data_quality_reporter import DataQualityReporter

# Initialize
dictionary = DataDictionary()
reporter = DataQualityReporter(dictionary)

# Validate a data record
data = {
    "symbol": "BTC",
    "price": 45000.50,
    "timestamp": "2025-01-03T22:03:36"
}

# Validate against standards
errors = dictionary.validate_data(data)
if errors["missing_required"]:
    print("Missing required fields:", errors["missing_required"])

# Generate quality report
report = reporter.generate_report(data, report_type="full")
print(f"Quality Score: {report['quality_score']['overall_score']}/100")

# Save report
reporter.save_report(report, format="json")
reporter.save_report(report, format="markdown")
```

## Components

### 1. Data Dictionary (`core/data_standards.py`)

The `DataDictionary` class defines:
- **Field Definitions**: Name, type, description, validation rules
- **Data Types**: FLOAT, STRING, INTEGER, DATETIME, BOOLEAN
- **Validation Rules**: Min/max values, patterns, required fields
- **Allowed Values**: For categorical fields (labels)

#### Key Methods

```python
# Get field definition
field = dictionary.get_field("price")
print(field.description)  # "Current price in USD"

# Validate single field
errors = dictionary.validate_field("price", 45000.50)

# Validate entire record
errors = dictionary.validate_data(data)

# Export as Markdown documentation
markdown = dictionary.export_markdown()
```

### 2. Quality Reporter (`analytics/data_quality_reporter.py`)

The `DataQualityReporter` class generates comprehensive quality reports:

#### Quality Metrics

1. **Completeness**: Are all required fields present?
2. **Validity**: Do values match standards and validation rules?
3. **Consistency**: Are logical relationships between fields correct?

#### Report Types

- **"full"**: Complete analysis with field-by-field details
- **"summary"**: Key metrics and recommendations
- **"quick"**: Fast analysis with basic scores

#### Key Methods

```python
# Generate report
report = reporter.generate_report(data, report_type="full")

# Save report
reporter.save_report(report, format="json")  # or "markdown"

# Batch reporting
batch_report = reporter.generate_batch_report([data1, data2, data3])
```

## Report Structure

### Quality Report JSON Structure

```json
{
  "report_metadata": {
    "generated_at": "2025-01-03T22:03:36",
    "data_source": "BTC",
    "report_type": "full",
    "report_version": "1.0"
  },
  "quality_score": {
    "overall_score": 95.5,
    "grade": "A",
    "components": {
      "completeness": 100.0,
      "validity": 95.0,
      "consistency": 90.0
    }
  },
  "completeness": {
    "total_fields": 14,
    "present_fields": 14,
    "completeness_percentage": 100.0,
    "required_completeness_percentage": 100.0,
    "grade": "A"
  },
  "validity": {
    "total_errors": 0,
    "validity_percentage": 100.0,
    "grade": "A"
  },
  "consistency": {
    "issues_count": 0,
    "consistency_percentage": 100.0,
    "grade": "A"
  },
  "recommendations": [
    "Data quality is excellent - maintain current standards"
  ]
}
```

## Integration with Existing Pipeline

The data standards system integrates seamlessly with your existing pipeline:

1. **Collection Phase**: Data is collected with standard fields
2. **Cleaning Phase**: Data is validated and cleaned
3. **Labeling Phase**: Labels are added according to standards
4. **Quality Reporting**: Reports validate against the dictionary

### Example: Add Quality Check to Pipeline

```python
from analytics.data_quality_reporter import DataQualityReporter

# After labeling
labeled_data = labeler_agent.label_all_cleaned_files()

# Generate quality reports
reporter = DataQualityReporter()
for record in labeled_data:
    report = reporter.generate_report(record)
    reporter.save_report(report)
```

## Data Dictionary Fields

### Base Data Fields
- `symbol`: Cryptocurrency symbol (required)
- `price`: Current price in USD (required)
- `lowest_24h`: Lowest price in 24h (optional)
- `highest_24h`: Highest price in 24h (optional)
- `price_change_24h`: 24h price change % (optional)
- `timestamp`: ISO 8601 timestamp (required)
- `source_exchange`: Exchange name (optional)

### Label Fields
- `price_movement`: Movement category (strong_up, up, sideways, down, strong_down)
- `volatility`: Volatility level (high, medium, low)
- `trend`: Trend direction (strong_bullish, bullish, neutral, bearish, strong_bearish)
- `price_category`: Price position (near_high, above_mid, below_mid, near_low)
- `change_magnitude`: Change magnitude (extreme, large, moderate, small, minimal)

### Metadata Fields
- `cleaned_at`: Timestamp when cleaned
- `labeled_at`: Timestamp when labeled

## Use Cases

### 1. Data Validation

```python
# Validate data before saving
errors = dictionary.validate_data(data)
if errors["missing_required"]:
    raise ValueError(f"Missing required fields: {errors['missing_required']}")
```

### 2. Quality Monitoring

```python
# Monitor quality over time
reports = []
for data in data_stream:
    report = reporter.generate_report(data)
    reports.append(report)
    
    if report["quality_score"]["overall_score"] < 80:
        logger.warning(f"Low quality data: {report['quality_score']['overall_score']}")
```

### 3. Documentation

```python
# Export data dictionary for documentation
markdown = dictionary.export_markdown()
with open("docs/data_dictionary.md", "w") as f:
    f.write(markdown)
```

### 4. Batch Analysis

```python
# Analyze multiple records at once
batch_report = reporter.generate_batch_report(all_data)
print(f"Average quality: {batch_report['aggregate_scores']['overall_average']}")
```

## File Locations

- **Data Dictionary**: `core/data_standards.py`
- **Quality Reporter**: `analytics/data_quality_reporter.py`
- **Report Generator Script**: `scripts/generate_quality_reports.py`
- **Generated Reports**: `data/quality_reports/`
- **Data Dictionary Export**: `data/quality_reports/data_dictionary.md`

## Next Steps

1. **Run the pipeline**: `python main.py`
2. **Generate reports**: `python scripts/generate_quality_reports.py`
3. **Review reports**: Check `data/quality_reports/` for JSON and Markdown reports
4. **Read data dictionary**: Open `data/quality_reports/data_dictionary.md`

## Interview Talking Points

When discussing this feature in interviews, highlight:

1. **Data Governance**: Establishing standards and documentation
2. **Automated Validation**: Reducing manual quality checks
3. **Comprehensive Reporting**: Multiple metrics and actionable recommendations
4. **Integration**: Works seamlessly with existing pipeline
5. **Documentation**: Self-documenting data dictionary

This demonstrates skills in:
- Data quality management
- Data governance
- Automated reporting
- Documentation
- Standards compliance

