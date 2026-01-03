"""
Configuration package for DonutAI crypto data pipeline.

INTERVIEW EXPLANATION:
This package centralizes all configuration management. This is a best practice because:
1. Single Source of Truth: All config in one place
2. Environment-based: Different configs for dev/prod
3. Type Safety: Settings can be validated
4. Security: Sensitive data (API keys) in .env files, not in code
"""

