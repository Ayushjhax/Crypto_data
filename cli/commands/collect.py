
import click
from pathlib import Path
from typing import Optional

from agents.collector_agent import CollectorAgent
from cli.utils import print_success, print_error, print_info, format_output
from utils.logger import setup_logger

logger = setup_logger(__name__)


@click.group()
def collect():
    pass


@collect.command()
@click.option('--symbol', '-s', multiple=True, help='Specific coin symbols to collect (e.g., BTC, ETH)')
@click.option('--save/--no-save', default=True, help='Save collected data to files')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def all(symbol, save, output_format):
    try:
        print_info("Starting data collection...")
        agent = CollectorAgent()
        
        if symbol:
            collected_data = []
            for sym in symbol:
                print_info(f"Collecting data for {sym}...")
                try:
                    data = agent.collector.collect_coin_data(sym)
                    if data:
                        collected_data.append(data)
                        if save:
                            agent.collector.save_data(data, format="json")
                        print_success(f"Collected data for {sym}")
                    else:
                        print_error(f"Failed to collect data for {sym}")
                except Exception as e:
                    print_error(f"Error collecting {sym}: {e}")
                    logger.error(f"Error collecting {sym}: {e}", exc_info=True)
        else:
            collected_data = agent.collect_all(save_to_file=save)
        
        stats = agent.get_stats()
        print_success(f"Collection complete!")
        print(f"\nStatistics:")
        print(format_output(stats, format=output_format))
        
        agent.collector.close()
        
    except Exception as e:
        print_error(f"Collection failed: {e}")
        logger.error(f"Collection failed: {e}", exc_info=True)
        raise click.Abort()


@collect.command()
@click.argument('symbol')
@click.option('--save/--no-save', default=True, help='Save collected data to file')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def coin(symbol, save, output_format):
    try:
        print_info(f"Collecting data for {symbol}...")
        agent = CollectorAgent()
        
        data = agent.collector.collect_coin_data(symbol)
        
        if data:
            if save:
                agent.collector.save_data(data, format="json")
            print_success(f"Collected data for {symbol}")
            print(f"\nData:")
            print(format_output(data, format=output_format))
        else:
            print_error(f"Failed to collect data for {symbol}")
        
        agent.collector.close()
        
    except Exception as e:
        print_error(f"Collection failed: {e}")
        logger.error(f"Collection failed: {e}", exc_info=True)
        raise click.Abort()


@collect.command()
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def list_coins(output_format):
    try:
        agent = CollectorAgent()
        coins = agent.get_coins_to_collect()
        
        print_info(f"Found {len(coins)} configured coins:")
        print(format_output(coins, format=output_format))
        
    except Exception as e:
        print_error(f"Error listing coins: {e}")
        logger.error(f"Error listing coins: {e}", exc_info=True)
        raise click.Abort()


@collect.command()
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def stats(output_format):
    try:
        agent = CollectorAgent()
        stats = agent.get_stats()
        
        print("Collection Statistics:")
        print(format_output(stats, format=output_format))
        
    except Exception as e:
        print_error(f"Error getting stats: {e}")
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise click.Abort()

