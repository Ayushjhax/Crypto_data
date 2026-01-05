# DonutAI CLI Usage Examples

## Quick Start - Run Everything

The easiest way to run everything:

```bash
python cli_entry.py run-all
```

This single command will:
1. ✅ Collect crypto data
2. ✅ Clean the data
3. ✅ Label the data
4. ✅ Evaluate data quality
5. ✅ Check for anomalies
6. ✅ Generate analytics summary
7. ✅ Generate reports
8. ✅ Show final status

## Common Usage Patterns

### 1. Run Everything (Recommended)
```bash
# Run complete workflow
python cli_entry.py run-all

# Run with custom analytics period
python cli_entry.py run-all --analytics-days 7

# Skip analytics if you only want the pipeline
python cli_entry.py run-all --skip-analytics
```

### 2. Run Just the Pipeline
```bash
# Complete pipeline only
python cli_entry.py pipeline
```

### 3. Individual Operations

#### Data Collection
```bash
# Collect all coins
python cli_entry.py collect all

# Collect specific coin
python cli_entry.py collect coin BTC

# List configured coins
python cli_entry.py collect list-coins
```

#### Data Cleaning
```bash
# Clean all raw files
python cli_entry.py clean all

# Clean specific file
python cli_entry.py clean file data/raw/BTC.json
```

#### Data Labeling
```bash
# Label all cleaned files
python cli_entry.py label all
```

#### Quality Checks
```bash
# Check quality of a file
python cli_entry.py quality check data/cleaned/BTC_cleaned.json

# Batch quality check
python cli_entry.py quality batch --data-dir cleaned

# View data standards
python cli_entry.py standards show
```

#### Analytics
```bash
# Get complete analytics summary
python cli_entry.py analytics summary --days 30

# Calculate DAU
python cli_entry.py analytics dau

# Get funnel analysis
python cli_entry.py analytics funnel --days 30

# Calculate retention
python cli_entry.py analytics retention --cohort-date 2025-01-01
```

#### Anomaly Detection
```bash
# Check all metrics for anomalies
python cli_entry.py anomaly check-all

# Check specific agent
python cli_entry.py anomaly check-agent collector
```

#### Reports
```bash
# Generate evaluation report
python cli_entry.py report evaluation --agent-type collector --days 7
```

### 4. System Information
```bash
# Check system status
python cli_entry.py status

# View data standards
python cli_entry.py standards show

# Export data dictionary
python cli_entry.py standards export
```

## Output Formats

Most commands support JSON output for programmatic use:

```bash
# Get stats as JSON
python cli_entry.py collect stats --output-format json

# Analytics as JSON
python cli_entry.py analytics summary --output-format json
```

## Error Handling

The CLI handles errors gracefully:
- If pipeline fails, analytics may still run (unless `--skip-analytics` is used)
- Individual step failures are logged but don't stop the entire process
- All errors are logged to the log file

## Help

Get help for any command:

```bash
# General help
python cli_entry.py --help

# Command group help
python cli_entry.py collect --help
python cli_entry.py analytics --help

# Specific command help
python cli_entry.py collect all --help
python cli_entry.py analytics dau --help
```

## Typical Workflow

### Daily Operations
```bash
# Run everything daily
python cli_entry.py run-all
```

### Weekly Review
```bash
# Generate weekly reports
python cli_entry.py report evaluation --days 7
python cli_entry.py analytics summary --days 7
```

### Troubleshooting
```bash
# Check for anomalies
python cli_entry.py anomaly check-all

# Check system status
python cli_entry.py status

# Validate data
python cli_entry.py standards validate data/raw/BTC.json
```

## Tips

1. **Use `run-all` for daily operations** - It's the most comprehensive command
2. **Use JSON output for automation** - Combine with scripts for automated workflows
3. **Check status regularly** - Use `status` command to monitor system health
4. **Monitor anomalies** - Set up scheduled `anomaly check-all` runs
5. **Review analytics weekly** - Use `analytics summary` to track trends

