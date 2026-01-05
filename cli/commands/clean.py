"""
CLI commands for data cleaning.
"""

import click
from pathlib import Path
from typing import Optional

from agents.cleaner_agent import CleanerAgent
from config.settings import RAW_DATA_DIR, CLEANED_DATA_DIR
from cli.utils import print_success, print_error, print_info, print_warning, format_output, load_json_file
from utils.logger import setup_logger

logger = setup_logger(__name__)


@click.group()
def clean():
    """Data cleaning commands."""
    pass


@clean.command()
@click.option('--save/--no-save', default=True, help='Save cleaned data to files')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def all(save, output_format):
    """Clean all raw data files."""
    try:
        print_info("Starting data cleaning for all raw files...")
        agent = CleanerAgent()
        
        cleaned_data = agent.clean_all_raw_files(save_to_file=save)
        
        if cleaned_data:
            print_success(f"Cleaned {len(cleaned_data)} files")
            
            # Display statistics
            stats = agent.get_stats()
            print(f"\nCleaning Statistics:")
            print(format_output(stats, format=output_format))
        else:
            print_warning("No data was cleaned. Check if raw data files exist.")
        
    except Exception as e:
        print_error(f"Cleaning failed: {e}")
        logger.error(f"Cleaning failed: {e}", exc_info=True)
        raise click.Abort()


@clean.command()
@click.argument('filepath', type=click.Path(exists=True, path_type=Path))
@click.option('--save/--no-save', default=True, help='Save cleaned data to file')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def file(filepath, save, output_format):
    """Clean a specific raw data file."""
    try:
        print_info(f"Cleaning data from {filepath.name}...")
        agent = CleanerAgent()
        
        # Load raw data
        raw_data = load_json_file(filepath)
        if not raw_data:
            print_error(f"Failed to load data from {filepath}")
            raise click.Abort()
        
        # Clean the data
        cleaned_data = agent.cleaner.clean_data(raw_data)
        
        if cleaned_data:
            if save:
                agent.cleaner.save_cleaned_data(cleaned_data, format="json")
            print_success(f"Cleaned data from {filepath.name}")
            print(f"\nCleaned Data:")
            print(format_output(cleaned_data, format=output_format))
        else:
            print_error(f"Failed to clean data from {filepath.name}")
        
    except Exception as e:
        print_error(f"Cleaning failed: {e}")
        logger.error(f"Cleaning failed: {e}", exc_info=True)
        raise click.Abort()


@clean.command()
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def stats(output_format):
    """Show cleaning statistics."""
    try:
        agent = CleanerAgent()
        stats = agent.get_stats()
        
        print("Cleaning Statistics:")
        print(format_output(stats, format=output_format))
        
    except Exception as e:
        print_error(f"Error getting stats: {e}")
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise click.Abort()


@clean.command()
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def list_files(output_format):
    """List all raw data files available for cleaning."""
    try:
        raw_files = list(RAW_DATA_DIR.glob("*.json"))
        raw_files = [f for f in raw_files if not f.name.startswith("all_coins")]
        
        if raw_files:
            file_list = [{"filename": f.name, "size_bytes": f.stat().st_size} for f in raw_files]
            print_info(f"Found {len(raw_files)} raw data files:")
            print(format_output(file_list, format=output_format))
        else:
            print_warning("No raw data files found")
        
    except Exception as e:
        print_error(f"Error listing files: {e}")
        logger.error(f"Error listing files: {e}", exc_info=True)
        raise click.Abort()

