# Product Analytics System for DonutAI

## Overview

This document describes the product analytics system integrated into DonutAI. The system tracks user interactions, pipeline usage, and calculates key product metrics mentioned in product analytics job descriptions:

- **DAU** (Daily Active Users)
- **Conversion rates**
- **Funnel analysis**
- **Retention rates**

---

## What Was Added

### 1. Database Schema (`database/schema.sql`)

Added analytics tables to track user events and sessions:

- **`analytics_events`**: Tracks all user events (pipeline_start, collection_complete, etc.)
- **`analytics_sessions`**: Tracks pipeline runs with funnel completion status

### 2. Event Tracker (`analytics/event_tracker.py`)

The `EventTracker` class implements event tracking:

- **`start_pipeline_session()`**: Creates a new session when pipeline starts
- **`track_phase_completion()`**: Tracks when each phase completes (collection, cleaning, labeling, evaluation)
- **`complete_pipeline_session()`**: Marks session as complete/failed
- **`track_event()`**: Generic event tracking method

### 3. Metrics Calculator (`analytics/metrics_calculator.py`)

The `MetricsCalculator` class calculates product metrics:

- **`calculate_dau()`**: Daily Active Users (unique pipeline runs per day)
- **`get_dau_timeseries()`**: DAU over time (for charts)
- **`calculate_conversion_rate()`**: Conversion rate between two events
- **`calculate_funnel()`**: Funnel analysis with drop-off rates
- **`calculate_retention()`**: Retention rates (Day 1, 7, 30)
- **`get_pipeline_funnel()`**: Standard pipeline funnel
- **`get_feature_usage()`**: Feature usage statistics
- **`get_summary()`**: Complete analytics summary

### 4. Integration (`main.py`)

Event tracking is integrated into the main pipeline:

- Tracks session start at pipeline beginning
- Tracks phase completion for each pipeline phase
- Marks session as complete/failed at end

### 5. View Analytics Script (`scripts/view_analytics.py`)

A script to view all analytics metrics in the terminal.

---

## Key Metrics Explained

### DAU (Daily Active Users)

**What it measures**: Number of unique pipeline runs per day.

**Why it matters**: Shows daily engagement with the product.

**How to calculate**:
```python
from analytics.metrics_calculator import MetricsCalculator

calculator = MetricsCalculator()
dau = calculator.calculate_dau()  # Today's DAU
```

### Conversion Rate

**What it measures**: Percentage of users who complete one step and proceed to the next.

**Why it matters**: Identifies where users drop off in the pipeline.

**Example**: Collection → Cleaning conversion shows how many users who collect data also clean it.

**How to calculate**:
```python
conversion_rate = calculator.calculate_conversion_rate(
    'collection_complete',  # Start event
    'cleaning_complete',    # End event
    date_range=(start_date, end_date)
)
```

### Funnel Analysis

**What it measures**: User progression through pipeline steps with drop-off rates.

**Why it matters**: Identifies bottlenecks and optimization opportunities.

**Pipeline funnel steps**:
1. Pipeline Start
2. Collection Complete
3. Cleaning Complete
4. Labeling Complete
5. Evaluation Complete

**How to calculate**:
```python
funnel = calculator.get_pipeline_funnel(days=30)
# Returns: {step_name: {users_reached, dropoff_rate, conversion_rate}}
```

### Retention

**What it measures**: Percentage of users who return after N days.

**Why it matters**: Shows long-term user engagement and product stickiness.

**Example**: Day 7 retention = % of users who run pipeline again 7 days after first run.

**How to calculate**:
```python
retention = calculator.calculate_retention(
    cohort_date=date.today() - timedelta(days=7),
    days=[1, 7, 30]
)
```

---

## Usage

### View Analytics in Terminal

```bash
python scripts/view_analytics.py
```

This displays:
- Current DAU and DAU timeseries
- Conversion rates for all funnel steps
- Complete funnel analysis
- Feature usage statistics
- Retention rates
- Complete summary (JSON)

### Use in Code

```python
from analytics.metrics_calculator import MetricsCalculator

calculator = MetricsCalculator()

# Get DAU
dau = calculator.calculate_dau()

# Get conversion rate
conversion = calculator.calculate_conversion_rate(
    'pipeline_start', 'evaluation_complete'
)

# Get funnel
funnel = calculator.get_pipeline_funnel(30)

# Get summary
summary = calculator.get_summary(30)

calculator.close()
```

---

## Database Location

Analytics data is stored in: `data/analytics.db`

This is a SQLite database that contains:
- `analytics_events` table
- `analytics_sessions` table

---

## Interview Talking Points

When discussing this in interviews:

1. **"I implemented product analytics tracking to measure DAU, conversion, funnel, and retention"**
   - Show understanding of key product metrics

2. **"I built an event tracking system that captures user interactions throughout the pipeline"**
   - Demonstrate event-driven architecture knowledge

3. **"I created a metrics calculation engine that computes conversion rates and funnel drop-offs"**
   - Show data analysis skills

4. **"I integrated analytics tracking into the existing pipeline without disrupting functionality"**
   - Show integration and architecture skills

5. **"The system uses SQL for efficient querying and supports time-series analysis"**
   - Show database and SQL knowledge

---

## Files Modified/Created

### Created:
- `analytics/event_tracker.py` - Event tracking system
- `analytics/metrics_calculator.py` - Metrics calculation engine
- `scripts/view_analytics.py` - Analytics viewer script
- `PRODUCT_ANALYTICS.md` - This documentation

### Modified:
- `database/schema.sql` - Added analytics tables
- `main.py` - Integrated event tracking
- `analytics/__init__.py` - Exported new modules

---

## Next Steps (Optional Enhancements)

1. **Dashboard**: Create a web dashboard using Flask/FastAPI
2. **Visualizations**: Add charts using Matplotlib or Plotly
3. **Alerts**: Set up alerts for metric thresholds
4. **Export**: Add CSV/Excel export functionality
5. **Advanced Metrics**: Add cohort analysis, LTV, etc.

---

## References

This implementation follows patterns from:
- Google Analytics
- Mixpanel
- Amplitude
- Product analytics best practices

---

## Notes

- Analytics tracking is non-intrusive - it doesn't affect pipeline performance
- All tracking happens asynchronously during pipeline execution
- Database is created automatically on first use
- Metrics can be calculated for any date range

