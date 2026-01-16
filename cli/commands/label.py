
import click
from pathlib import Path

from agents.labeler_agent import LabelerAgent
from config.settings import CLEANED_DATA_DIR
from cli.utils import print_success, print_error, print_info, print_warning, format_output, load_json_file
from utils.logger import setup_logger

logger = setup_logger(__name__)


@click.group()
def label():
    pass


@label.command()
@click.option('--save/--no-save', default=True, help='Save labeled data to files')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def all(save, output_format):
    try:
        print_info("Starting data labeling for all cleaned files...")
        agent = LabelerAgent()
        
        labeled_data = agent.label_all_cleaned_files(save_to_file=save)
        
        if labeled_data:
            print_success(f"Labeled {len(labeled_data)} files")
            
            stats = agent.get_stats()
            print(f"\nLabeling Statistics:")
            print(format_output(stats, format=output_format))
        else:
            print_warning("No data was labeled. Check if cleaned data files exist.")
        
    except Exception as e:
        print_error(f"Labeling failed: {e}")
        logger.error(f"Labeling failed: {e}", exc_info=True)
        raise click.Abort()


@label.command()
@click.argument('filepath', type=click.Path(exists=True, path_type=Path))
@click.option('--save/--no-save', default=True, help='Save labeled data to file')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def file(filepath, save, output_format):
    try:
        print_info(f"Labeling data from {filepath.name}...")
        agent = LabelerAgent()
        
        cleaned_data = load_json_file(filepath)
        if not cleaned_data:
            print_error(f"Failed to load data from {filepath}")
            raise click.Abort()
        
        labeled_data = agent.labeler.label_data(cleaned_data)
        
        if labeled_data:
            if save:
                agent.labeler.save_labeled_data(labeled_data, format="json")
            print_success(f"Labeled data from {filepath.name}")
            print(f"\nLabeled Data:")
            print(format_output(labeled_data, format=output_format))
        else:
            print_error(f"Failed to label data from {filepath.name}")
        
    except Exception as e:
        print_error(f"Labeling failed: {e}")
        logger.error(f"Labeling failed: {e}", exc_info=True)
        raise click.Abort()


@label.command()
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def stats(output_format):
    try:
        agent = LabelerAgent()
        stats = agent.get_stats()
        
        print("Labeling Statistics:")
        print(format_output(stats, format=output_format))
        
    except Exception as e:
        print_error(f"Error getting stats: {e}")
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise click.Abort()


@label.command()
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def list_files(output_format):
    try:
        cleaned_files = list(CLEANED_DATA_DIR.glob("*.json"))
        cleaned_files = [f for f in cleaned_files if not f.name.startswith("all_coins")]
        
        if cleaned_files:
            file_list = [{"filename": f.name, "size_bytes": f.stat().st_size} for f in cleaned_files]
            print_info(f"Found {len(cleaned_files)} cleaned data files:")
            print(format_output(file_list, format=output_format))
        else:
            print_warning("No cleaned data files found")
        
    except Exception as e:
        print_error(f"Error listing files: {e}")
        logger.error(f"Error listing files: {e}", exc_info=True)
        raise click.Abort()

