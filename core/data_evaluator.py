
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import math

from utils.logger import setup_logger

logger = setup_logger(__name__)


class DataEvaluator:
    
    def __init__(self):
        self.evaluation_stats = {
            'evaluations_performed': 0,
            'high_quality_count': 0,  # overall_score >= 0.8
            'medium_quality_count': 0,  # 0.5 <= overall_score < 0.8
            'low_quality_count': 0  # overall_score < 0.5
        }
    
    def evaluate_collector_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        issues = []  # List to collect problems found
        evaluated_fields = []  # List of fields we checked
        
        required_fields = ['symbol', 'price', 'market_cap', 'volume_24h']
        
        missing_fields = [
            f for f in required_fields 
            if f not in data or data[f] is None
        ]
        
        completeness_score = 1.0 - (len(missing_fields) / len(required_fields))
        
        if missing_fields:
            issues.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        evaluated_fields.extend(required_fields)
        
        accuracy_issues = []
        
        if 'price' in data and data['price']:
            if data['price'] <= 0:
                accuracy_issues.append("Price must be positive")
            if data['price'] > 1000000:  # $1M seems very high for crypto
                accuracy_issues.append("Price seems unusually high (possible data error)")
        
        if 'market_cap' in data and data['market_cap']:
            if data['market_cap'] < 0:
                accuracy_issues.append("Market cap cannot be negative")
        
        if 'volume_24h' in data and data['volume_24h']:
            if data['volume_24h'] < 0:
                accuracy_issues.append("Volume cannot be negative")
        
        accuracy_score = 1.0 if not accuracy_issues else max(0.0, 1.0 - len(accuracy_issues) * 0.2)
        issues.extend(accuracy_issues)  # Add accuracy issues to main issues list
        
        consistency_issues = []
        
        if 'price_change_24h' in data and data['price_change_24h']:
            if abs(data['price_change_24h']) > 100:
                consistency_issues.append("Price change percentage seems unrealistic (>100%)")
        
        consistency_score = 1.0 if not consistency_issues else 0.7
        issues.extend(consistency_issues)
        
        overall_score = (
            completeness_score * 0.4 +  # 40% weight
            accuracy_score * 0.4 +       # 40% weight
            consistency_score * 0.2      # 20% weight
        )
        
        recommendations = self._generate_recommendations(
            completeness_score, accuracy_score, consistency_score, issues
        )
        
        evaluation = {
            'completeness_score': round(completeness_score, 3),  # Round to 3 decimal places
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
    
    def evaluate_cleaner_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        evaluated_fields = []
        
        if 'cleaned_at' not in data:
            issues.append("Missing cleaning metadata (cleaned_at field)")
        else:
            evaluated_fields.append('cleaned_at')
        
        expected_cleaned_fields = ['symbol', 'price', 'market_cap', 'volume_24h', 'price_change_24h']
        missing_fields = [
            f for f in expected_cleaned_fields 
            if f not in data or data[f] is None
        ]
        
        completeness_score = 1.0 - (len(missing_fields) / len(expected_cleaned_fields))
        
        if missing_fields:
            issues.append(f"Missing fields after cleaning: {', '.join(missing_fields)}")
        
        evaluated_fields.extend(expected_cleaned_fields)
        
        accuracy_issues = []
        
        for field in expected_cleaned_fields:
            if field in data:
                value = data[field]
                if isinstance(value, float):
                    if math.isnan(value) or math.isinf(value):
                        accuracy_issues.append(f"{field} contains NaN or Inf value (should be cleaned)")
        
        accuracy_score = 1.0 if not accuracy_issues else 0.5
        issues.extend(accuracy_issues)
        
        consistency_issues = []
        
        if 'price' in data:
            if not isinstance(data['price'], (int, float)):
                consistency_issues.append("Price should be numeric type")
        
        consistency_score = 1.0 if not consistency_issues else 0.8
        issues.extend(consistency_issues)
        
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
        issues = []
        evaluated_fields = []
        
        expected_labels = ['price_movement', 'volatility', 'trend', 'price_category', 'change_magnitude']
        
        missing_labels = [
            l for l in expected_labels 
            if l not in data or data[l] is None
        ]
        
        completeness_score = 1.0 - (len(missing_labels) / len(expected_labels))
        
        if missing_labels:
            issues.append(f"Missing labels: {', '.join(missing_labels)}")
        
        evaluated_fields.extend(expected_labels)
        evaluated_fields.append('symbol')  # Also check base data field
        
        accuracy_issues = []
        
        if 'price_movement' in data and 'price_change_24h' in data:
            label = data['price_movement']
            change = data.get('price_change_24h')
            
            if change is not None:
                if change > 5 and label != 'strong_up':
                    accuracy_issues.append("price_movement label may not match price_change_24h value")
                elif change < -5 and label != 'strong_down':
                    accuracy_issues.append("price_movement label may not match price_change_24h value")
        
        accuracy_score = 1.0 if not accuracy_issues else 0.7
        issues.extend(accuracy_issues)
        
        consistency_issues = []
        
        valid_movements = ['strong_up', 'up', 'sideways', 'down', 'strong_down', 'unknown']
        
        if 'price_movement' in data:
            if data['price_movement'] not in valid_movements:
                consistency_issues.append(
                    f"Invalid price_movement value: {data['price_movement']} "
                    f"(expected one of: {', '.join(valid_movements)})"
                )
        
        consistency_score = 1.0 if not consistency_issues else 0.8
        issues.extend(consistency_issues)
        
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
        recommendations = []
        
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
        
        if not issues:
            recommendations.append(
                "Data quality is excellent - maintain current standards"
            )
        
        return recommendations
    
    def _update_stats(self, overall_score: float):
        self.evaluation_stats['evaluations_performed'] += 1
        
        if overall_score >= 0.8:
            self.evaluation_stats['high_quality_count'] += 1
        elif overall_score >= 0.5:
            self.evaluation_stats['medium_quality_count'] += 1
        else:
            self.evaluation_stats['low_quality_count'] += 1
    
    def get_evaluation_stats(self) -> Dict[str, Any]:
        return self.evaluation_stats.copy()

