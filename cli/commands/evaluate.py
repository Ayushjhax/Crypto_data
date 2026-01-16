
import click
from pathlib import Path

from agents.evaluator_agent import EvaluatorAgent
from config.settings import RAW_DATA_DIR, CLEANED_DATA_DIR, LABELED_DATA_DIR
from cli.utils import print_success, print_error, print_info, format_output, load_json_file
from utils.logger import setup_logger

logger = setup_logger(__name__)


@click.group()
def evaluate():
    pass


@evaluate.command()
@click.option('--db-path', default='data/evaluations.db', help='Path to evaluation database')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def all(db_path, output_format):
    try:
        print_info("Starting evaluation of all pipeline outputs...")
        agent = EvaluatorAgent(db_path=db_path)
        
        results = agent.evaluate_all_pipeline_outputs()
        
        collector_evals = len(results.get('collector_evaluations', []))
        cleaner_evals = len(results.get('cleaner_evaluations', []))
        labeler_evals = len(results.get('labeler_evaluations', []))
        
        print_success("Evaluation complete!")
        print(f"\nEvaluation Results:")
        print(f"  - Collector evaluations: {collector_evals}")
        print(f"  - Cleaner evaluations: {cleaner_evals}")
        print(f"  - Labeler evaluations: {labeler_evals}")
        print(f"  - Run ID: {results.get('run_id', 'N/A')}")
        
        stats = agent.get_stats()
        print(f"\nEvaluation Statistics:")
        print(format_output(stats, format=output_format))
        
        agent.close()
        
    except Exception as e:
        print_error(f"Evaluation failed: {e}")
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise click.Abort()


@evaluate.command()
@click.argument('filepath', type=click.Path(exists=True, path_type=Path))
@click.option('--agent-type', type=click.Choice(['collector', 'cleaner', 'labeler']), required=True,
              help='Type of agent that produced this data')
@click.option('--db-path', default='data/evaluations.db', help='Path to evaluation database')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def file(filepath, agent_type, db_path, output_format):
    try:
        print_info(f"Evaluating {agent_type} data from {filepath.name}...")
        agent = EvaluatorAgent(db_path=db_path)
        
        data = load_json_file(filepath)
        if not data:
            print_error(f"Failed to load data from {filepath}")
            raise click.Abort()
        
        if agent_type == 'collector':
            result = agent.evaluate_collector_output(data, str(filepath))
        elif agent_type == 'cleaner':
            result = agent.evaluate_cleaner_output(data, str(filepath))
        elif agent_type == 'labeler':
            result = agent.evaluate_labeler_output(data, str(filepath))
        else:
            print_error(f"Unknown agent type: {agent_type}")
            raise click.Abort()
        
        if result:
            print_success(f"Evaluation complete for {filepath.name}")
            print(f"\nEvaluation Result:")
            print(format_output(result, format=output_format))
        else:
            print_error(f"Evaluation failed for {filepath.name}")
        
        agent.close()
        
    except Exception as e:
        print_error(f"Evaluation failed: {e}")
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise click.Abort()


@evaluate.command()
@click.option('--db-path', default='data/evaluations.db', help='Path to evaluation database')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def stats(db_path, output_format):
    try:
        agent = EvaluatorAgent(db_path=db_path)
        stats = agent.get_stats()
        
        print("Evaluation Statistics:")
        print(format_output(stats, format=output_format))
        
        agent.close()
        
    except Exception as e:
        print_error(f"Error getting stats: {e}")
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise click.Abort()

