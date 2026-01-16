
import click
from datetime import date, timedelta

from analytics.metrics_calculator import MetricsCalculator
from cli.utils import print_success, print_error, print_info, format_output, format_percentage
from utils.logger import setup_logger

logger = setup_logger(__name__)


@click.group()
def analytics():
    pass


@analytics.command()
@click.option('--date', 'target_date_str', type=click.DateTime(formats=['%Y-%m-%d']), default=None,
              help='Date to calculate DAU for (YYYY-MM-DD), default: today')
@click.option('--db-path', default='data/analytics.db', help='Path to analytics database')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def dau(target_date_str, db_path, output_format):
    try:
        calculator = MetricsCalculator(db_path=db_path)
        
        target_date = target_date_str.date() if target_date_str else date.today()
        dau_value = calculator.calculate_dau(target_date)
        
        print_success(f"DAU for {target_date}: {dau_value}")
        
        if output_format == 'json':
            print(format_output({'date': target_date.isoformat(), 'dau': dau_value}, format=output_format))
        
        calculator.close()
        
    except Exception as e:
        print_error(f"Error calculating DAU: {e}")
        logger.error(f"Error calculating DAU: {e}", exc_info=True)
        raise click.Abort()


@analytics.command()
@click.option('--days', default=30, help='Number of days to retrieve')
@click.option('--db-path', default='data/analytics.db', help='Path to analytics database')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def dau_timeseries(days, db_path, output_format):
    try:
        calculator = MetricsCalculator(db_path=db_path)
        
        timeseries = calculator.get_dau_timeseries(days=days)
        
        print_info(f"DAU Time Series (last {days} days):")
        print(format_output(timeseries, format=output_format))
        
        calculator.close()
        
    except Exception as e:
        print_error(f"Error getting DAU timeseries: {e}")
        logger.error(f"Error getting DAU timeseries: {e}", exc_info=True)
        raise click.Abort()


@analytics.command()
@click.option('--start-event', required=True, help='Starting event name')
@click.option('--end-event', required=True, help='Ending event name')
@click.option('--start-date', type=click.DateTime(formats=['%Y-%m-%d']), default=None,
              help='Start date (YYYY-MM-DD)')
@click.option('--end-date', type=click.DateTime(formats=['%Y-%m-%d']), default=None,
              help='End date (YYYY-MM-DD)')
@click.option('--db-path', default='data/analytics.db', help='Path to analytics database')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def conversion(start_event, end_event, start_date, end_date, db_path, output_format):
    try:
        calculator = MetricsCalculator(db_path=db_path)
        
        date_range = None
        if start_date and end_date:
            date_range = (start_date.date(), end_date.date())
        
        rate = calculator.calculate_conversion_rate(start_event, end_event, date_range)
        
        print_success(f"Conversion rate ({start_event} → {end_event}): {format_percentage(rate)}")
        
        if output_format == 'json':
            print(format_output({
                'start_event': start_event,
                'end_event': end_event,
                'conversion_rate': rate,
                'date_range': date_range
            }, format=output_format))
        
        calculator.close()
        
    except Exception as e:
        print_error(f"Error calculating conversion rate: {e}")
        logger.error(f"Error calculating conversion rate: {e}", exc_info=True)
        raise click.Abort()


@analytics.command()
@click.option('--days', default=30, help='Number of days to analyze')
@click.option('--db-path', default='data/analytics.db', help='Path to analytics database')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def funnel(days, db_path, output_format):
    try:
        calculator = MetricsCalculator(db_path=db_path)
        
        funnel_data = calculator.get_pipeline_funnel(days=days)
        
        print_info(f"Pipeline Funnel Analysis (last {days} days):")
        print("\n" + "="*60)
        for step, data in funnel_data.items():
            print(f"\n{step}:")
            print(f"  Users Reached: {data['users_reached']}")
            print(f"  Drop-off Rate: {format_percentage(data['dropoff_rate'])}")
            print(f"  Conversion Rate: {format_percentage(data['conversion_rate'])}")
        
        if output_format == 'json':
            print("\n" + format_output(funnel_data, format=output_format))
        
        calculator.close()
        
    except Exception as e:
        print_error(f"Error calculating funnel: {e}")
        logger.error(f"Error calculating funnel: {e}", exc_info=True)
        raise click.Abort()


@analytics.command()
@click.option('--cohort-date', type=click.DateTime(formats=['%Y-%m-%d']), required=True,
              help='Cohort date (YYYY-MM-DD)')
@click.option('--days', default=[1, 7, 30], multiple=True, help='Retention days to calculate')
@click.option('--db-path', default='data/analytics.db', help='Path to analytics database')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def retention(cohort_date, days, db_path, output_format):
    try:
        calculator = MetricsCalculator(db_path=db_path)
        
        retention_days = list(days) if days else [1, 7, 30]
        retention_data = calculator.calculate_retention(cohort_date.date(), days=retention_days)
        
        print_info(f"Retention Rates for cohort {cohort_date.date()}:")
        print("\n" + "="*60)
        for day_key, rate in retention_data.items():
            day_num = day_key.replace('day_', '')
            print(f"Day {day_num} Retention: {format_percentage(rate)}")
        
        if output_format == 'json':
            print("\n" + format_output(retention_data, format=output_format))
        
        calculator.close()
        
    except Exception as e:
        print_error(f"Error calculating retention: {e}")
        logger.error(f"Error calculating retention: {e}", exc_info=True)
        raise click.Abort()


@analytics.command()
@click.option('--days', default=30, help='Number of days to analyze')
@click.option('--db-path', default='data/analytics.db', help='Path to analytics database')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def summary(days, db_path, output_format):
    try:
        calculator = MetricsCalculator(db_path=db_path)
        
        summary_data = calculator.get_summary(days=days)
        
        print_info(f"Analytics Summary (last {days} days):")
        print("\n" + "="*60)
        
        print(f"\nDaily Active Users (DAU):")
        print(f"  Current: {summary_data['dau']['current']}")
        
        print(f"\nPipeline Funnel:")
        for step, data in summary_data['funnel'].items():
            print(f"  {step}: {data['users_reached']} users ({format_percentage(data['conversion_rate'])} conversion)")
        
        print(f"\nConversion Rates:")
        for name, rate in summary_data['conversion'].items():
            print(f"  {name}: {format_percentage(rate)}")
        
        print(f"\nFeature Usage:")
        usage = summary_data['feature_usage']
        print(f"  Total Sessions: {usage['total_sessions']}")
        print(f"  Completed Sessions: {usage['completed_sessions']}")
        print(f"  Completion Rate: {format_percentage(usage['completion_rate'])}")
        print(f"  Avg Completion Time: {usage['avg_completion_hours']} hours")
        
        if output_format == 'json':
            print("\n" + format_output(summary_data, format=output_format))
        
        calculator.close()
        
    except Exception as e:
        print_error(f"Error getting summary: {e}")
        logger.error(f"Error getting summary: {e}", exc_info=True)
        raise click.Abort()

