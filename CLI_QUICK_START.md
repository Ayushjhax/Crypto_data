# CLI Quick Start Guide

## Installation

1. Install dependencies (including Click):
```bash
pip install -r requirements.txt
```

Or install Click separately:
```bash
pip install click>=8.1.0
```

## Quick Test

After installation, test the CLI:
```bash
python cli_entry.py --help
```

You should see all available command groups.

## Common Commands

### Run Everything (Recommended)
```bash
python cli_entry.py run-all
```

This runs the complete pipeline + analytics + reports + status. This is the **easiest way to run everything**!

### Run Complete Pipeline
```bash
python cli_entry.py pipeline
```

### Check System Status
```bash
python cli_entry.py status
```

### Data Collection
```bash
# Collect all coins
python cli_entry.py collect all

# Collect specific coin
python cli_entry.py collect coin BTC
```

### Data Quality Check
```bash
# Check quality of a file
python cli_entry.py quality check data/cleaned/BTC_cleaned.json

# View data standards
python cli_entry.py standards show
```

### Analytics
```bash
# Get analytics summary
python cli_entry.py analytics summary --days 30

# Calculate DAU
python cli_entry.py analytics dau

# Get funnel analysis
python cli_entry.py analytics funnel --days 30
```

### Anomaly Detection
```bash
# Check for anomalies
python cli_entry.py anomaly check-all
```

## Command Structure

All commands follow this pattern:
```bash
python cli_entry.py <command-group> <subcommand> [options]
```

Get help for any command:
```bash
python cli_entry.py <command-group> --help
python cli_entry.py <command-group> <subcommand> --help
```

## Example Workflow

```bash
# 1. Collect data
python cli_entry.py collect all

# 2. Clean data
python cli_entry.py clean all

# 3. Label data
python cli_entry.py label all

# 4. Evaluate
python cli_entry.py evaluate all

# 5. Check for anomalies
python cli_entry.py anomaly check-all

# 6. View analytics
python cli_entry.py analytics summary --days 7
```

For detailed documentation, see `CLI_README.md`.

