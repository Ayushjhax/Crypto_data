# DonutAI CLI Documentation

A comprehensive command-line interface for managing the DonutAI crypto data pipeline.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make the CLI executable (optional):
```bash
chmod +x cli_entry.py
```

## Usage

### Basic Usage

Run commands using Python:
```bash
python cli_entry.py <command> [subcommand] [options]
```

Or use as a module:
```bash
python -m cli.main <command> [subcommand] [options]
```

### Command Groups

The CLI is organized into the following command groups:

#### 1. Data Collection (`collect`)
- **`collect all`** - Collect data for all configured coins
- **`collect coin <SYMBOL>`** - Collect data for a specific coin
- **`collect list-coins`** - List all configured coins
- **`collect stats`** - Show collection statistics

**Examples:**
```bash
# Collect all coins
python cli_entry.py collect all

# Collect specific coins
python cli_entry.py collect all --symbol BTC --symbol ETH

# Collect single coin
python cli_entry.py collect coin BTC

# List configured coins
python cli_entry.py collect list-coins
```

#### 2. Data Cleaning (`clean`)
- **`clean all`** - Clean all raw data files
- **`clean file <FILEPATH>`** - Clean a specific file
- **`clean list-files`** - List available raw data files
- **`clean stats`** - Show cleaning statistics

**Examples:**
```bash
# Clean all raw files
python cli_entry.py clean all

# Clean specific file
python cli_entry.py clean file data/raw/BTC_20250103.json

# List files to clean
python cli_entry.py clean list-files
```

#### 3. Data Labeling (`label`)
- **`label all`** - Label all cleaned data files
- **`label file <FILEPATH>`** - Label a specific file
- **`label list-files`** - List available cleaned data files
- **`label stats`** - Show labeling statistics

**Examples:**
```bash
# Label all cleaned files
python cli_entry.py label all

# Label specific file
python cli_entry.py label file data/cleaned/BTC_cleaned_20250103.json
```

#### 4. Data Evaluation (`evaluate`)
- **`evaluate all`** - Evaluate all pipeline outputs
- **`evaluate file <FILEPATH> --agent-type <TYPE>`** - Evaluate a specific file
- **`evaluate stats`** - Show evaluation statistics

**Examples:**
```bash
# Evaluate all outputs
python cli_entry.py evaluate all

# Evaluate specific file
python cli_entry.py evaluate file data/raw/BTC.json --agent-type collector
```

#### 5. Data Quality Checks (`quality`)
- **`quality check <FILEPATH>`** - Check quality for a specific file
- **`quality batch --data-dir <DIR>`** - Check quality for all files in a directory
- **`quality standards`** - Show data standards and dictionary

**Examples:**
```bash
# Check single file quality
python cli_entry.py quality check data/cleaned/BTC_cleaned.json

# Batch quality check
python cli_entry.py quality batch --data-dir cleaned

# View data standards
python cli_entry.py quality standards
```

#### 6. Product Analytics (`analytics`)
- **`analytics dau [--date DATE]`** - Calculate Daily Active Users
- **`analytics dau-timeseries [--days N]`** - Get DAU time series
- **`analytics conversion --start-event EVENT --end-event EVENT`** - Calculate conversion rate
- **`analytics funnel [--days N]`** - Calculate pipeline funnel
- **`analytics retention --cohort-date DATE`** - Calculate retention rates
- **`analytics summary [--days N]`** - Get complete analytics summary

**Examples:**
```bash
# Calculate DAU for today
python cli_entry.py analytics dau

# Get DAU for specific date
python cli_entry.py analytics dau --date 2025-01-03

# Get DAU time series
python cli_entry.py analytics dau-timeseries --days 30

# Calculate conversion rate
python cli_entry.py analytics conversion --start-event pipeline_start --end-event evaluation_complete

# Get funnel analysis
python cli_entry.py analytics funnel --days 30

# Calculate retention
python cli_entry.py analytics retention --cohort-date 2025-01-01

# Get complete summary
python cli_entry.py analytics summary --days 30
```

#### 7. Anomaly Detection (`anomaly`)
- **`anomaly check-all`** - Check all metrics for anomalies
- **`anomaly check-agent <AGENT_TYPE>`** - Check specific agent
- **`anomaly stats`** - Show anomaly detection statistics

**Examples:**
```bash
# Check all metrics
python cli_entry.py anomaly check-all

# Check specific agent
python cli_entry.py anomaly check-agent collector

# With custom threshold
python cli_entry.py anomaly check-all --threshold 0.8 --lookback-days 14
```

#### 8. Report Generation (`report`)
- **`report evaluation [--agent-type TYPE] [--days N]`** - Generate evaluation report
- **`report quality-summary`** - Generate quality summary report

**Examples:**
```bash
# Generate evaluation report
python cli_entry.py report evaluation --agent-type collector --days 7

# Generate quality summary
python cli_entry.py report quality-summary
```

#### 9. Data Standards (`standards`)
- **`standards show`** - Show data dictionary
- **`standards field <FIELD_NAME>`** - Show specific field details
- **`standards export [--output-file FILE]`** - Export data dictionary
- **`standards validate <FILEPATH>`** - Validate file against dictionary

**Examples:**
```bash
# Show all standards
python cli_entry.py standards show

# Show specific field
python cli_entry.py standards field symbol

# Export dictionary
python cli_entry.py standards export --output-file data_dictionary.json

# Validate file
python cli_entry.py standards validate data/raw/BTC.json
```

### Utility Commands

#### Run Everything (Recommended)
```bash
python cli_entry.py run-all
```

This is the **recommended command** that runs everything:
1. Complete pipeline (collect → clean → label → evaluate → anomaly check)
2. Analytics summary generation
3. Report generation
4. Final system status

**Options:**
- `--skip-analytics` - Skip analytics generation
- `--skip-reports` - Skip report generation
- `--analytics-days N` - Number of days for analytics (default: 30)

**Examples:**
```bash
# Run everything
python cli_entry.py run-all

# Run everything but skip analytics
python cli_entry.py run-all --skip-analytics

# Run everything with custom analytics period
python cli_entry.py run-all --analytics-days 7
```

#### Run Complete Pipeline
```bash
python cli_entry.py pipeline
```

This runs the complete pipeline: collect → clean → label → evaluate → anomaly check

#### System Status
```bash
python cli_entry.py status
```

Shows overall system status including file counts and database sizes.

### Output Formats

Most commands support `--output-format` option:
- **`table`** (default) - Human-readable table format
- **`json`** - JSON format for programmatic use

**Example:**
```bash
python cli_entry.py collect stats --output-format json
```

### Common Options

- **`--save/--no-save`** - Control whether to save output files (default: save)
- **`--output-format`** - Output format (table/json)
- **`--db-path`** - Custom database path (for evaluation/analytics commands)

## Job Description Alignment

This CLI covers all aspects of the job description:

1. **✅ Use agents to collect, clean, and label crypto training data**
   - `collect`, `clean`, `label` commands

2. **✅ Perform basic data quality checks**
   - `quality check`, `quality batch` commands

3. **✅ Assist in data processing for the critic agent evaluation system**
   - `evaluate` commands for evaluation system

4. **✅ Organize data standards and data dictionaries**
   - `standards` commands for data dictionary management

5. **✅ Produce simple data reports**
   - `report` commands for generating reports

6. **✅ Support product tracking implementation**
   - `analytics` commands for product metrics

7. **✅ Conduct basic data analysis and reporting (DAU, conversion, funnel, retention)**
   - `analytics dau`, `analytics conversion`, `analytics funnel`, `analytics retention` commands

8. **✅ Monitor product metrics for anomalies**
   - `anomaly` commands for anomaly detection

9. **✅ Promptly communicate findings to engineering team**
   - Anomaly alerts are sent automatically when anomalies are detected

## Examples

### Complete Workflow

```bash
# 1. Collect data
python cli_entry.py collect all

# 2. Clean data
python cli_entry.py clean all

# 3. Label data
python cli_entry.py label all

# 4. Evaluate quality
python cli_entry.py evaluate all

# 5. Check for anomalies
python cli_entry.py anomaly check-all

# 6. Generate reports
python cli_entry.py report evaluation --days 7
python cli_entry.py analytics summary --days 30
```

### Quick Quality Check

```bash
# Check quality of a specific file
python cli_entry.py quality check data/cleaned/BTC_cleaned.json

# Batch check all cleaned files
python cli_entry.py quality batch --data-dir cleaned
```

### Analytics Dashboard

```bash
# Get complete analytics summary
python cli_entry.py analytics summary --days 30

# Get funnel analysis
python cli_entry.py analytics funnel --days 30

# Get retention rates
python cli_entry.py analytics retention --cohort-date 2025-01-01
```

## Help

Get help for any command:
```bash
python cli_entry.py --help
python cli_entry.py collect --help
python cli_entry.py analytics --help
```

## Architecture

The CLI is organized using a modular structure:

```
cli/
├── __init__.py
├── main.py              # Main entry point
├── utils.py             # Shared utilities
└── commands/
    ├── __init__.py
    ├── collect.py       # Collection commands
    ├── clean.py         # Cleaning commands
    ├── label.py         # Labeling commands
    ├── evaluate.py      # Evaluation commands
    ├── quality.py       # Quality check commands
    ├── analytics.py     # Analytics commands
    ├── anomaly.py        # Anomaly detection commands
    ├── report.py         # Report generation commands
    └── standards.py      # Data standards commands
```

This modular structure makes it easy to:
- Add new commands
- Maintain existing commands
- Test individual components
- Understand the codebase

