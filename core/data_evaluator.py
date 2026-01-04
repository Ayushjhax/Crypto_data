"""
Core evaluation logic for data quality assessment.

INTERVIEW EXPLANATION:
This is the "critic agent" - it evaluates data quality from
collector, cleaner, and labeler agents. It scores data on
multiple dimensions: completeness, accuracy, consistency.

The critic agent pattern:
1. Primary agents (collector, cleaner, labeler) do the work
2. Critic agent (this module) evaluates their output quality
3. Scores are stored in database for analysis
4. Reports help identify and fix quality issues
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import math

from utils.logger import setup_logger

logger = setup_logger(__name__)


class DataEvaluator:
    """
    Core evaluator that assesses data quality.
    
    INTERVIEW EXPLANATION:
    This class implements the critic agent logic. It evaluates
    data quality and provides scores and recommendations.
    
    Evaluation dimensions:
    - Completeness: Are required fields present?
    - Accuracy: Are values correct and within expected ranges?
    - Consistency: Does data match expected structure/format?
    """
    
    def __init__(self):
        """Initialize the data evaluator."""
        # Track statistics for reporting
        self.evaluation_stats = {
            'evaluations_performed': 0,
            'high_quality_count': 0,  # overall_score >= 0.8
            'medium_quality_count': 0,  # 0.5 <= overall_score < 0.8
            'low_quality_count': 0  # overall_score < 0.5
        }
    
    def evaluate_collector_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate data from collector agent.
        
        INTERVIEW EXPLANATION:
        Evaluates raw collected data for:
        - Completeness: Are required fields present?
        - Accuracy: Are values in expected ranges?
        - Consistency: Does data match expected structure?
        
        Args:
            data: Dictionary containing collected crypto data
        
        Returns:
            Dictionary with evaluation scores and details
        """
        issues = []  # List to collect problems found
        evaluated_fields = []  # List of fields we checked
        
        # ============================================================
        # 1. COMPLETENESS CHECK: Are required fields present?
        # ============================================================
        # Define fields that must be present for valid data
        required_fields = ['symbol', 'price', 'market_cap', 'volume_24h']
        
        # Find which required fields are missing or None
        missing_fields = [
            f for f in required_fields 
            if f not in data or data[f] is None
        ]
        
        # Calculate completeness score: 1.0 = all fields present, 0.0 = no fields present
        # Example: 3 out of 4 fields present = 0.75 score
        completeness_score = 1.0 - (len(missing_fields) / len(required_fields))
        
        # Add to issues list if fields are missing
        if missing_fields:
            issues.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Track which fields we evaluated
        evaluated_fields.extend(required_fields)
        
        # ============================================================
        # 2. ACCURACY CHECK: Are values correct and reasonable?
        # ============================================================
        accuracy_issues = []
        
        # Check price: Must be positive and reasonable
        if 'price' in data and data['price']:
            if data['price'] <= 0:
                accuracy_issues.append("Price must be positive")
            # Sanity check: Very high prices might indicate data error
            if data['price'] > 1000000:  # $1M seems very high for crypto
                accuracy_issues.append("Price seems unusually high (possible data error)")
        
        # Check market cap: Cannot be negative
        if 'market_cap' in data and data['market_cap']:
            if data['market_cap'] < 0:
                accuracy_issues.append("Market cap cannot be negative")
        
        # Check volume: Cannot be negative
        if 'volume_24h' in data and data['volume_24h']:
            if data['volume_24h'] < 0:
                accuracy_issues.append("Volume cannot be negative")
        
        # Calculate accuracy score
        # Each issue reduces score by 0.2, minimum score is 0.0
        accuracy_score = 1.0 if not accuracy_issues else max(0.0, 1.0 - len(accuracy_issues) * 0.2)
        issues.extend(accuracy_issues)  # Add accuracy issues to main issues list
        
        # ============================================================
        # 3. CONSISTENCY CHECK: Does data make sense together?
        # ============================================================
        consistency_issues = []
        
        # Check if price_change_24h is consistent (reasonable range)
        if 'price_change_24h' in data and data['price_change_24h']:
            # Price changes over 100% in 24h are very unusual
            if abs(data['price_change_24h']) > 100:
                consistency_issues.append("Price change percentage seems unrealistic (>100%)")
        
        # Calculate consistency score
        consistency_score = 1.0 if not consistency_issues else 0.7
        issues.extend(consistency_issues)
        
        # ============================================================
        # 4. CALCULATE OVERALL SCORE
        # ============================================================
        # Weighted average: Completeness and accuracy are more important
        overall_score = (
            completeness_score * 0.4 +  # 40% weight
            accuracy_score * 0.4 +       # 40% weight
            consistency_score * 0.2      # 20% weight
        )
        
        # ============================================================
        # 5. GENERATE RECOMMENDATIONS
        # ============================================================
        recommendations = self._generate_recommendations(
            completeness_score, accuracy_score, consistency_score, issues
        )
        
        # ============================================================
        # 6. BUILD EVALUATION RESULT DICTIONARY
        # ============================================================
        evaluation = {
            'completeness_score': round(completeness_score, 3),  # Round to 3 decimal places
            'accuracy_score': round(accuracy_score, 3),
            'consistency_score': round(consistency_score, 3),
            'overall_score': round(overall_score, 3),
            'evaluated_fields': evaluated_fields,
            'issues_found': issues,
            'recommendations': recommendations,
            # Store detailed metrics as JSON string
            'metrics_json': json.dumps({
                'missing_fields_count': len(missing_fields),
                'accuracy_issues_count': len(accuracy_issues),
                'consistency_issues_count': len(consistency_issues)
            })
        }
        
        # Update statistics
        self._update_stats(overall_score)
        
        return evaluation
    
    def evaluate_cleaner_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate data from cleaner agent.
        
        INTERVIEW EXPLANATION:
        Evaluates cleaned data - checks if cleaning was successful:
        - Are all expected fields still present after cleaning?
        - Are invalid values (NaN, Inf) removed?
        - Are data types correct?
        
        Args:
            data: Dictionary containing cleaned crypto data
        
        Returns:
            Dictionary with evaluation scores and details
        """
        issues = []
        evaluated_fields = []
        
        # ============================================================
        # 1. COMPLETENESS: Check if cleaned data has all expected fields
        # ============================================================
        # Check if cleaning metadata exists (proves data went through cleaner)
        if 'cleaned_at' not in data:
            issues.append("Missing cleaning metadata (cleaned_at field)")
        else:
            evaluated_fields.append('cleaned_at')
        
        # Expected fields after cleaning (same as before, but should all be present)
        expected_cleaned_fields = ['symbol', 'price', 'market_cap', 'volume_24h', 'price_change_24h']
        missing_fields = [
            f for f in expected_cleaned_fields 
            if f not in data or data[f] is None
        ]
        
        completeness_score = 1.0 - (len(missing_fields) / len(expected_cleaned_fields))
        
        if missing_fields:
            issues.append(f"Missing fields after cleaning: {', '.join(missing_fields)}")
        
        evaluated_fields.extend(expected_cleaned_fields)
        
        # ============================================================
        # 2. ACCURACY: Check for invalid values (NaN, Inf, etc.)
        # ============================================================
        accuracy_issues = []
        
        # Check for NaN (Not a Number) or infinite values
        # These should be removed/fixed during cleaning
        for field in expected_cleaned_fields:
            if field in data:
                value = data[field]
                # Check if value is a float (numbers)
                if isinstance(value, float):
                    # math.isnan() checks if value is NaN
                    # math.isinf() checks if value is infinite
                    if math.isnan(value) or math.isinf(value):
                        accuracy_issues.append(f"{field} contains NaN or Inf value (should be cleaned)")
        
        # Accuracy score: If any invalid values found, score is lower
        accuracy_score = 1.0 if not accuracy_issues else 0.5
        issues.extend(accuracy_issues)
        
        # ============================================================
        # 3. CONSISTENCY: Check data types are correct
        # ============================================================
        consistency_issues = []
        
        # Price should be a number (int or float)
        if 'price' in data:
            if not isinstance(data['price'], (int, float)):
                consistency_issues.append("Price should be numeric type")
        
        consistency_score = 1.0 if not consistency_issues else 0.8
        issues.extend(consistency_issues)
        
        # ============================================================
        # 4. OVERALL SCORE (weighted average)
        # ============================================================
        # Accuracy is more important for cleaned data (50% weight)
        overall_score = (
            completeness_score * 0.3 +  # 30% weight
            accuracy_score * 0.5 +       # 50% weight (most important for cleaned data)
            consistency_score * 0.2      # 20% weight
        )
        
        recommendations = self._generate_recommendations(
            completeness_score, accuracy_score, consistency_score, issues
        )
        
        evaluation = {
            'completeness_score': round(completeness_score, 3),
            'accuracy_score': round(accuracy_score, 3),
            'consistency_score': round(consistency_score, 3),
            'overall_score': round(overall_score, 3),
            'evaluated_fields': evaluated_fields,
            'issues_found': issues,
            'recommendations': recommendations,
            'metrics_json': json.dumps({
                'missing_fields_count': len(missing_fields),
                'accuracy_issues_count': len(accuracy_issues),
                'consistency_issues_count': len(consistency_issues)
            })
        }
        
        self._update_stats(overall_score)
        return evaluation
    
    def evaluate_labeler_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate data from labeler agent.
        
        INTERVIEW EXPLANATION:
        Evaluates labeled data - checks if labels are present and correct:
        - Are all expected labels present?
        - Do labels match the underlying data values?
        - Are label values in expected format?
        
        Args:
            data: Dictionary containing labeled crypto data
        
        Returns:
            Dictionary with evaluation scores and details
        """
        issues = []
        evaluated_fields = []
        
        # ============================================================
        # 1. COMPLETENESS: Check if all expected labels are present
        # ============================================================
        # Labels that should be added by labeler agent
        expected_labels = ['price_movement', 'volatility', 'trend', 'price_category', 'change_magnitude']
        
        # Find missing labels
        missing_labels = [
            l for l in expected_labels 
            if l not in data or data[l] is None
        ]
        
        # Calculate completeness score
        completeness_score = 1.0 - (len(missing_labels) / len(expected_labels))
        
        if missing_labels:
            issues.append(f"Missing labels: {', '.join(missing_labels)}")
        
        evaluated_fields.extend(expected_labels)
        evaluated_fields.append('symbol')  # Also check base data field
        
        # ============================================================
        # 2. ACCURACY: Validate label values against data
        # ============================================================
        accuracy_issues = []
        
        # Check if price_movement label matches price_change_24h value
        if 'price_movement' in data and 'price_change_24h' in data:
            label = data['price_movement']
            change = data.get('price_change_24h')
            
            # Validate label matches data logic
            if change is not None:
                # If price change is > 5%, label should be 'strong_up'
                if change > 5 and label != 'strong_up':
                    accuracy_issues.append("price_movement label may not match price_change_24h value")
                # If price change is < -5%, label should be 'strong_down'
                elif change < -5 and label != 'strong_down':
                    accuracy_issues.append("price_movement label may not match price_change_24h value")
        
        accuracy_score = 1.0 if not accuracy_issues else 0.7
        issues.extend(accuracy_issues)
        
        # ============================================================
        # 3. CONSISTENCY: Check label format/values are valid
        # ============================================================
        consistency_issues = []
        
        # Valid values for price_movement label
        valid_movements = ['strong_up', 'up', 'sideways', 'down', 'strong_down', 'unknown']
        
        if 'price_movement' in data:
            # Check if label value is in the list of valid values
            if data['price_movement'] not in valid_movements:
                consistency_issues.append(
                    f"Invalid price_movement value: {data['price_movement']} "
                    f"(expected one of: {', '.join(valid_movements)})"
                )
        
        consistency_score = 1.0 if not consistency_issues else 0.8
        issues.extend(consistency_issues)
        
        # ============================================================
        # 4. OVERALL SCORE
        # ============================================================
        overall_score = (
            completeness_score * 0.4 +  # 40% weight
            accuracy_score * 0.4 +       # 40% weight
            consistency_score * 0.2      # 20% weight
        )
        
        recommendations = self._generate_recommendations(
            completeness_score, accuracy_score, consistency_score, issues
        )
        
        evaluation = {
            'completeness_score': round(completeness_score, 3),
            'accuracy_score': round(accuracy_score, 3),
            'consistency_score': round(consistency_score, 3),
            'overall_score': round(overall_score, 3),
            'evaluated_fields': evaluated_fields,
            'issues_found': issues,
            'recommendations': recommendations,
            'metrics_json': json.dumps({
                'missing_labels_count': len(missing_labels),
                'accuracy_issues_count': len(accuracy_issues),
                'consistency_issues_count': len(consistency_issues)
            })
        }
        
        self._update_stats(overall_score)
        return evaluation
    
    def _generate_recommendations(
        self,
        completeness_score: float,
        accuracy_score: float,
        consistency_score: float,
        issues: List[str]
    ) -> List[str]:
        """
        Generate actionable recommendations based on evaluation scores.
        
        INTERVIEW EXPLANATION:
        This method analyzes the scores and issues to provide
        actionable recommendations for improving data quality.
        
        Args:
            completeness_score: Completeness score (0.0 to 1.0)
            accuracy_score: Accuracy score (0.0 to 1.0)
            consistency_score: Consistency score (0.0 to 1.0)
            issues: List of issues found
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Generate recommendations based on low scores
        if completeness_score < 0.8:
            recommendations.append(
                "Improve data collection to ensure all required fields are present"
            )
        
        if accuracy_score < 0.8:
            recommendations.append(
                "Add validation rules to catch invalid values during collection"
            )
        
        if consistency_score < 0.8:
            recommendations.append(
                "Review data transformation logic for consistency issues"
            )
        
        # If no issues, congratulate!
        if not issues:
            recommendations.append(
                "Data quality is excellent - maintain current standards"
            )
        
        return recommendations
    
    def _update_stats(self, overall_score: float):
        """
        Update evaluation statistics based on overall score.
        
        INTERVIEW EXPLANATION:
        Tracks statistics for reporting:
        - How many evaluations performed
        - Quality distribution (high/medium/low)
        
        Args:
            overall_score: Overall quality score (0.0 to 1.0)
        """
        self.evaluation_stats['evaluations_performed'] += 1
        
        # Categorize quality based on score
        if overall_score >= 0.8:
            self.evaluation_stats['high_quality_count'] += 1
        elif overall_score >= 0.5:
            self.evaluation_stats['medium_quality_count'] += 1
        else:
            self.evaluation_stats['low_quality_count'] += 1
    
    def get_evaluation_stats(self) -> Dict[str, Any]:
        """
        Get evaluation statistics.
        
        Returns:
            Dictionary with evaluation statistics
        """
        return self.evaluation_stats.copy()

