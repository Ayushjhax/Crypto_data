"""
CLI commands for data standards and dictionary management.
"""

import click
from pathlib import Path
import json

from core.data_standards import DataDictionary
from cli.utils import print_success, print_error, print_info, print_warning, format_output, save_json_file
from utils.logger import setup_logger

logger = setup_logger(__name__)


@click.group()
def standards():
    """Data standards and dictionary commands."""
    pass


@standards.command()
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def show(output_format):
    """Show data dictionary and standards."""
    try:
        dictionary = DataDictionary()
        
        print("Data Dictionary & Standards")
        print("="*60)
        print(f"Version: {dictionary.version}")
        print(f"Last Updated: {dictionary.last_updated}")
        print(f"Total Fields: {len(dictionary.fields)}")
        
        if output_format == 'json':
            fields_dict = {name: field.to_dict() for name, field in dictionary.fields.items()}
            print(format_output({
                'version': dictionary.version,
                'last_updated': dictionary.last_updated,
                'total_fields': len(dictionary.fields),
                'fields': fields_dict
            }, format=output_format))
        else:
            print("\nField Definitions:")
            for name, field in dictionary.fields.items():
                print(f"\n  {name}:")
                print(f"    Type: {field.data_type.value}")
                print(f"    Required: {field.required}")
                print(f"    Description: {field.description}")
                if field.example:
                    print(f"    Example: {field.example}")
                if field.validation_rules:
                    print(f"    Validation Rules: {field.validation_rules}")
        
    except Exception as e:
        print_error(f"Error showing standards: {e}")
        logger.error(f"Error showing standards: {e}", exc_info=True)
        raise click.Abort()


@standards.command()
@click.argument('field_name')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def field(field_name, output_format):
    """Show details for a specific field."""
    try:
        dictionary = DataDictionary()
        
        if field_name not in dictionary.fields:
            print_error(f"Field '{field_name}' not found in dictionary")
            raise click.Abort()
        
        field_def = dictionary.fields[field_name]
        
        print(f"Field: {field_name}")
        print("="*60)
        
        if output_format == 'json':
            print(format_output(field_def.to_dict(), format=output_format))
        else:
            print(f"Type: {field_def.data_type.value}")
            print(f"Required: {field_def.required}")
            print(f"Description: {field_def.description}")
            if field_def.example:
                print(f"Example: {field_def.example}")
            if field_def.source:
                print(f"Source: {field_def.source}")
            if field_def.validation_rules:
                print(f"Validation Rules:")
                for rule, value in field_def.validation_rules.items():
                    print(f"  - {rule}: {value}")
            if field_def.allowed_values:
                print(f"Allowed Values: {', '.join(field_def.allowed_values)}")
        
    except Exception as e:
        print_error(f"Error showing field: {e}")
        logger.error(f"Error showing field: {e}", exc_info=True)
        raise click.Abort()


@standards.command()
@click.option('--output-file', type=click.Path(path_type=Path), default=None,
              help='Output file path (default: data_dictionary.json)')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def export(output_file, output_format):
    """Export data dictionary to JSON file."""
    try:
        dictionary = DataDictionary()
        
        if not output_file:
            output_file = Path("data_dictionary.json")
        
        fields_dict = {name: field.to_dict() for name, field in dictionary.fields.items()}
        export_data = {
            'version': dictionary.version,
            'last_updated': dictionary.last_updated,
            'fields': fields_dict
        }
        
        if save_json_file(export_data, output_file):
            print_success(f"Data dictionary exported to {output_file}")
        else:
            print_error(f"Failed to export data dictionary")
            raise click.Abort()
        
    except Exception as e:
        print_error(f"Error exporting dictionary: {e}")
        logger.error(f"Error exporting dictionary: {e}", exc_info=True)
        raise click.Abort()


@standards.command()
@click.argument('filepath', type=click.Path(exists=True, path_type=Path))
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def validate(filepath, output_format):
    """Validate data file against data dictionary."""
    try:
        import json
        dictionary = DataDictionary()
        
        # Load data file
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Validate
        errors = dictionary.validate_data(data)
        
        total_errors = sum(len(err_list) for err_list in errors.values())
        
        if total_errors == 0:
            print_success(f"Data file {filepath.name} is valid according to data dictionary")
        else:
            print_warning(f"Found {total_errors} validation error(s) in {filepath.name}")
            print("\nValidation Errors:")
            for error_type, error_list in errors.items():
                if error_list:
                    print(f"\n  {error_type}:")
                    for error in error_list:
                        print(f"    - {error}")
        
        if output_format == 'json':
            print(format_output(errors, format=output_format))
        
    except Exception as e:
        print_error(f"Error validating file: {e}")
        logger.error(f"Error validating file: {e}", exc_info=True)
        raise click.Abort()

