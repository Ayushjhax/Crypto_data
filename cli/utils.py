
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys

from utils.logger import setup_logger

logger = setup_logger(__name__)


def format_output(data: Any, format: str = "table") -> str:
    if format == "json":
        return json.dumps(data, indent=2, default=str)
    elif format == "table":
        return format_table(data)
    else:
        return str(data)


def format_table(data: Any) -> str:
    if isinstance(data, dict):
        lines = []
        max_key_len = max(len(str(k)) for k in data.keys()) if data else 0
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, indent=2)
            else:
                value_str = str(value)
            lines.append(f"{str(key):<{max_key_len}} : {value_str}")
        return "\n".join(lines)
    elif isinstance(data, list):
        if not data:
            return "No data"
        if isinstance(data[0], dict):
            headers = list(data[0].keys())
            lines = []
            header_line = " | ".join(str(h) for h in headers)
            lines.append(header_line)
            lines.append("-" * len(header_line))
            for item in data:
                row = " | ".join(str(item.get(h, "")) for h in headers)
                lines.append(row)
            return "\n".join(lines)
        else:
            return "\n".join(str(item) for item in data)
    else:
        return str(data)


def print_success(message: str):
    print(f"✅ {message}")


def print_error(message: str):
    print(f"❌ {message}", file=sys.stderr)


def print_warning(message: str):
    print(f"⚠️  {message}")


def print_info(message: str):
    print(f"ℹ️  {message}")


def load_json_file(filepath: Path) -> Optional[Dict[str, Any]]:
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return None


def save_json_file(data: Any, filepath: Path) -> bool:
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        logger.error(f"Error saving {filepath}: {e}")
        return False


def format_timestamp(timestamp: Optional[datetime]) -> str:
    if timestamp is None:
        return "N/A"
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def format_percentage(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}%"


def format_number(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}"

