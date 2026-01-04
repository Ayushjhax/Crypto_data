"""
Data standards and data dictionary definitions.

INTERVIEW EXPLANATION:
This module defines:
1. Data Dictionary: Complete documentation of all fields
2. Data Standards: Validation rules and conventions
3. Field Definitions: Type, constraints, examples for each field

This is essential for:
- Ensuring data consistency across the pipeline
- Automated validation
- Documentation for stakeholders
- Quality reporting
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import re

from utils.logger import setup_logger

logger = setup_logger(__name__)


class DataType(Enum):
    """Supported data types."""
    FLOAT = "float"
    STRING = "string"
    INTEGER = "integer"
    DATETIME = "datetime"
    BOOLEAN = "boolean"


@dataclass
class FieldDefinition:
    """
    Definition of a single data field in the dictionary.
    
    INTERVIEW EXPLANATION:
    This dataclass encapsulates all information about a field:
    - What it is (name, type, description)
    - How to validate it (rules, constraints)
    - Where it comes from (source)
    - Examples for documentation
    """
    name: str
    data_type: DataType
    description: str
    required: bool
    example: Any
    validation_rules: Dict[str, Any]
    source: str
    allowed_values: Optional[List[str]] = None  # For categorical fields
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['data_type'] = self.data_type.value
        return result


class DataDictionary:
    """
    Manages the complete data dictionary for crypto data.
    
    INTERVIEW EXPLANATION:
    This class serves as the single source of truth for:
    - What fields exist in our data
    - What each field means
    - How to validate each field
    - What values are acceptable
    
    Benefits:
    1. Documentation: Clear understanding of data structure
    2. Validation: Automated checks against standards
    3. Consistency: Same rules applied everywhere
    4. Onboarding: New team members understand data quickly
    """
    
    def __init__(self):
        """Initialize data dictionary with all field definitions."""
        self.fields = self._initialize_fields()
        self.version = "1.0"
        self.last_updated = "2025-01-03"
    
    def _initialize_fields(self) -> Dict[str, FieldDefinition]:
        """Initialize all field definitions."""
        return {
            "symbol": FieldDefinition(
                name="symbol",
                data_type=DataType.STRING,
                description="Cryptocurrency symbol (e.g., BTC, ETH, SOL)",
                required=True,
                example="BTC",
                validation_rules={
                    "pattern": "^[A-Z]{2,10}$",
                    "uppercase": True,
                    "min_length": 2,
                    "max_length": 10
                },
                source="API response: 'symbol' field"
            ),
            "price": FieldDefinition(
                name="price",
                data_type=DataType.FLOAT,
                description="Current price in USD",
                required=True,
                example=45000.50,
                validation_rules={
                    "min": 0,
                    "max": 1000000000,  # $1B upper bound
                    "precision": 2  # Decimal places
                },
                source="API response: 'last' or 'price' field"
            ),
            "lowest_24h": FieldDefinition(
                name="lowest_24h",
                data_type=DataType.FLOAT,
                description="Lowest price in the last 24 hours (USD)",
                required=False,
                example=44000.00,
                validation_rules={
                    "min": 0,
                    "max": 1000000000
                },
                source="API response: 'lowest' field"
            ),
            "highest_24h": FieldDefinition(
                name="highest_24h",
                data_type=DataType.FLOAT,
                description="Highest price in the last 24 hours (USD)",
                required=False,
                example=46000.00,
                validation_rules={
                    "min": 0,
                    "max": 1000000000
                },
                source="API response: 'highest' field"
            ),
            "price_change_24h": FieldDefinition(
                name="price_change_24h",
                data_type=DataType.FLOAT,
                description="24-hour price change percentage",
                required=False,
                example=2.5,
                validation_rules={
                    "min": -100,  # Can't lose more than 100%
                    "max": 1000   # Upper bound for new coins
                },
                source="API response: 'daily_change_percentage' or 'price_change_24h' field"
            ),
            "timestamp": FieldDefinition(
                name="timestamp",
                data_type=DataType.DATETIME,
                description="ISO 8601 timestamp when data was collected",
                required=True,
                example="2025-01-03T22:03:36.123456",
                validation_rules={
                    "format": "ISO8601"
                },
                source="Generated at collection time"
            ),
            "source_exchange": FieldDefinition(
                name="source_exchange",
                data_type=DataType.STRING,
                description="Exchange or data source name",
                required=False,
                example="binance",
                validation_rules={
                    "lowercase": True,
                    "max_length": 50
                },
                source="API response: 'source_exchange' field"
            ),
            # Labeled data fields
            "price_movement": FieldDefinition(
                name="price_movement",
                data_type=DataType.STRING,
                description="Price movement category label",
                required=False,
                example="strong_up",
                validation_rules={},
                source="Generated by labeler agent",
                allowed_values=["strong_up", "up", "sideways", "down", "strong_down", "unknown"]
            ),
            "volatility": FieldDefinition(
                name="volatility",
                data_type=DataType.STRING,
                description="Volatility category label",
                required=False,
                example="medium",
                validation_rules={},
                source="Generated by labeler agent",
                allowed_values=["high", "medium", "low", "unknown"]
            ),
            "trend": FieldDefinition(
                name="trend",
                data_type=DataType.STRING,
                description="Trend direction label",
                required=False,
                example="bullish",
                validation_rules={},
                source="Generated by labeler agent",
                allowed_values=["strong_bullish", "bullish", "neutral", "bearish", "strong_bearish"]
            ),
            "price_category": FieldDefinition(
                name="price_category",
                data_type=DataType.STRING,
                description="Price position relative to 24h range",
                required=False,
                example="above_mid",
                validation_rules={},
                source="Generated by labeler agent",
                allowed_values=["near_high", "above_mid", "below_mid", "near_low", "unknown"]
            ),
            "change_magnitude": FieldDefinition(
                name="change_magnitude",
                data_type=DataType.STRING,
                description="Magnitude of price change",
                required=False,
                example="moderate",
                validation_rules={},
                source="Generated by labeler agent",
                allowed_values=["extreme", "large", "moderate", "small", "minimal", "unknown"]
            ),
            # Metadata fields
            "cleaned_at": FieldDefinition(
                name="cleaned_at",
                data_type=DataType.DATETIME,
                description="ISO timestamp when data was cleaned",
                required=False,
                example="2025-01-03T22:03:36.123456",
                validation_rules={"format": "ISO8601"},
                source="Added by cleaner agent"
            ),
            "labeled_at": FieldDefinition(
                name="labeled_at",
                data_type=DataType.DATETIME,
                description="ISO timestamp when data was labeled",
                required=False,
                example="2025-01-03T22:03:36.123456",
                validation_rules={"format": "ISO8601"},
                source="Added by labeler agent"
            )
        }
    
    def get_dictionary(self) -> Dict[str, Dict[str, Any]]:
        """
        Export complete data dictionary as JSON-serializable dictionary.
        
        Returns:
            Dictionary mapping field names to their definitions
        """
        return {
            name: field.to_dict()
            for name, field in self.fields.items()
        }
    
    def get_field(self, field_name: str) -> Optional[FieldDefinition]:
        """Get definition for a specific field."""
        return self.fields.get(field_name)
    
    def validate_field(self, field_name: str, value: Any) -> List[str]:
        """
        Validate a single field value against its definition.
        
        Args:
            field_name: Name of the field to validate
            value: Value to validate
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        if field_name not in self.fields:
            return [f"Unknown field: {field_name}"]
        
        field_def = self.fields[field_name]
        
        # Check required fields
        if field_def.required and (value is None or value == ""):
            errors.append(f"{field_name} is required but is missing or empty")
            return errors  # Can't validate further if required field is missing
        
        # Skip validation if value is None and field is optional
        if value is None:
            return errors
        
        # Type validation
        type_error = self._validate_type(value, field_def.data_type)
        if type_error:
            errors.append(type_error)
        
        # Validation rules
        rule_errors = self._validate_rules(value, field_def.validation_rules, field_name)
        errors.extend(rule_errors)
        
        # Allowed values check (for categorical fields)
        if field_def.allowed_values and value not in field_def.allowed_values:
            errors.append(
                f"{field_name}: value '{value}' not in allowed values: {field_def.allowed_values}"
            )
        
        return errors
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate complete data record against dictionary.
        
        Args:
            data: Data dictionary to validate
        
        Returns:
            Dictionary with validation results:
            - "missing_required": List of missing required fields
            - "type_errors": List of type mismatch errors
            - "validation_errors": List of validation rule violations
            - "unknown_fields": List of fields not in dictionary
        """
        errors = {
            "missing_required": [],
            "type_errors": [],
            "validation_errors": [],
            "unknown_fields": []
        }
        
        # Check for unknown fields
        for field_name in data:
            if field_name not in self.fields:
                errors["unknown_fields"].append(field_name)
        
        # Validate each field in dictionary
        for field_name, field_def in self.fields.items():
            # Check required fields
            if field_def.required:
                if field_name not in data or data[field_name] is None:
                    errors["missing_required"].append(f"{field_name} is required")
                    continue  # Skip further validation for missing required fields
            
            # Validate field if present
            if field_name in data:
                field_errors = self.validate_field(field_name, data[field_name])
                
                # Categorize errors
                for error in field_errors:
                    if "type" in error.lower() or "expected" in error.lower():
                        errors["type_errors"].append(error)
                    else:
                        errors["validation_errors"].append(error)
        
        return errors
    
    def _validate_type(self, value: Any, expected_type: DataType) -> Optional[str]:
        """Validate value type matches expected type."""
        if expected_type == DataType.FLOAT:
            if not isinstance(value, (int, float)):
                return f"Expected float, got {type(value).__name__}"
        elif expected_type == DataType.STRING:
            if not isinstance(value, str):
                return f"Expected string, got {type(value).__name__}"
        elif expected_type == DataType.INTEGER:
            if not isinstance(value, int):
                return f"Expected integer, got {type(value).__name__}"
        elif expected_type == DataType.DATETIME:
            if not isinstance(value, str):
                return f"Expected datetime string, got {type(value).__name__}"
            # Basic ISO8601 format check
            iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
            if not re.match(iso_pattern, value):
                return f"Expected ISO8601 datetime format, got: {value}"
        elif expected_type == DataType.BOOLEAN:
            if not isinstance(value, bool):
                return f"Expected boolean, got {type(value).__name__}"
        
        return None
    
    def _validate_rules(self, value: Any, rules: Dict[str, Any], field_name: str) -> List[str]:
        """Validate value against validation rules."""
        errors = []
        
        # Min/Max for numeric values
        if isinstance(value, (int, float)):
            if "min" in rules and value < rules["min"]:
                errors.append(f"{field_name}: value {value} is below minimum {rules['min']}")
            if "max" in rules and value > rules["max"]:
                errors.append(f"{field_name}: value {value} is above maximum {rules['max']}")
        
        # String validations
        if isinstance(value, str):
            if "min_length" in rules and len(value) < rules["min_length"]:
                errors.append(
                    f"{field_name}: length {len(value)} is below minimum {rules['min_length']}"
                )
            if "max_length" in rules and len(value) > rules["max_length"]:
                errors.append(
                    f"{field_name}: length {len(value)} is above maximum {rules['max_length']}"
                )
            if "pattern" in rules:
                if not re.match(rules["pattern"], value):
                    errors.append(f"{field_name}: value '{value}' doesn't match pattern {rules['pattern']}")
            if "uppercase" in rules and rules["uppercase"] and not value.isupper():
                errors.append(f"{field_name}: value should be uppercase")
            if "lowercase" in rules and rules["lowercase"] and not value.islower():
                errors.append(f"{field_name}: value should be lowercase")
        
        return errors
    
    def export_markdown(self) -> str:
        """
        Export data dictionary as Markdown documentation.
        
        Returns:
            Markdown formatted string
        """
        lines = [
            "# Data Dictionary",
            "",
            f"**Version:** {self.version}",
            f"**Last Updated:** {self.last_updated}",
            "",
            "## Field Definitions",
            ""
        ]
        
        # Group fields by category
        base_fields = ["symbol", "price", "lowest_24h", "highest_24h", "price_change_24h", 
                      "timestamp", "source_exchange"]
        label_fields = ["price_movement", "volatility", "trend", "price_category", "change_magnitude"]
        metadata_fields = ["cleaned_at", "labeled_at"]
        
        for category, field_names in [
            ("Base Data Fields", base_fields),
            ("Label Fields", label_fields),
            ("Metadata Fields", metadata_fields)
        ]:
            lines.append(f"### {category}")
            lines.append("")
            
            for field_name in field_names:
                if field_name in self.fields:
                    field = self.fields[field_name]
                    lines.extend([
                        f"#### `{field.name}`",
                        "",
                        f"- **Type:** `{field.data_type.value}`",
                        f"- **Required:** {'Yes' if field.required else 'No'}",
                        f"- **Description:** {field.description}",
                        f"- **Example:** `{field.example}`",
                        f"- **Source:** {field.source}",
                    ])
                    
                    if field.validation_rules:
                        lines.append("- **Validation Rules:**")
                        for rule, value in field.validation_rules.items():
                            lines.append(f"  - {rule}: {value}")
                    
                    if field.allowed_values:
                        lines.append(f"- **Allowed Values:** {', '.join(field.allowed_values)}")
                    
                    lines.append("")
        
        return "\n".join(lines)

