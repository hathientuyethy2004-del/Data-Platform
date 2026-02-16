"""
Data Quality Checks
Quality validation functions for lakehouse data
"""

from typing import Dict, List, Any
from datetime import datetime
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from configs.logging_config import setup_logging


logger = setup_logging(__name__)


class DataQualityChecker:
    """Performs quality checks on DataFrames"""
    
    def __init__(self):
        self.logger = logger
        self.checks_history = []
    
    def check_null_values(
        self,
        df: DataFrame,
        column: str,
        threshold_percent: float = 5.0,
    ) -> Dict[str, Any]:
        """
        Check null value percentage in a column
        
        Args:
            df: DataFrame to check
            column: Column name
            threshold_percent: Maximum allowed null percentage
        
        Returns:
            Dictionary with check results
        """
        total_count = df.count()
        null_count = df.filter(F.col(column).isNull()).count()
        null_percent = (null_count / total_count) * 100 if total_count > 0 else 0
        
        passed = null_percent <= threshold_percent
        
        result = {
            'check_type': 'null_values',
            'column': column,
            'total_records': total_count,
            'null_records': null_count,
            'null_percentage': round(null_percent, 2),
            'threshold_percent': threshold_percent,
            'passed': passed,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        status = '✅' if passed else '❌'
        self.logger.info(
            f"{status} Null check '{column}': {null_percent:.2f}% "
            f"(threshold: {threshold_percent}%)"
        )
        
        self.checks_history.append(result)
        return result
    
    def check_duplicates(
        self,
        df: DataFrame,
        key_columns: List[str],
    ) -> Dict[str, Any]:
        """
        Check for duplicate records
        
        Args:
            df: DataFrame to check
            key_columns: Columns that define uniqueness
        
        Returns:
            Dictionary with check results
        """
        total_count = df.count()
        unique_count = df.dropDuplicates(key_columns).count()
        duplicate_count = total_count - unique_count
        duplicate_percent = (duplicate_count / total_count) * 100 if total_count > 0 else 0
        
        passed = duplicate_count == 0
        
        result = {
            'check_type': 'duplicates',
            'key_columns': key_columns,
            'total_records': total_count,
            'unique_records': unique_count,
            'duplicate_records': duplicate_count,
            'duplicate_percentage': round(duplicate_percent, 2),
            'passed': passed,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        status = '✅' if passed else '⚠️'
        self.logger.info(
            f"{status} Duplicate check on {key_columns}: "
            f"{duplicate_count} duplicates found"
        )
        
        self.checks_history.append(result)
        return result
    
    def check_data_types(
        self,
        df: DataFrame,
        expected_types: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Check if columns have expected data types
        
        Args:
            df: DataFrame to check
            expected_types: Dict mapping column names to expected type names
        
        Returns:
            Dictionary with check results
        """
        actual_types = {field.name: field.dataType.simpleString() for field in df.schema}
        
        mismatches = []
        for col, expected_type in expected_types.items():
            if col not in actual_types:
                mismatches.append({'column': col, 'error': 'column_missing'})
            elif actual_types[col] != expected_type:
                mismatches.append({
                    'column': col,
                    'expected': expected_type,
                    'actual': actual_types[col],
                })
        
        passed = len(mismatches) == 0
        
        result = {
            'check_type': 'data_types',
            'total_columns': len(expected_types),
            'mismatches': mismatches,
            'passed': passed,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        status = '✅' if passed else '❌'
        self.logger.info(
            f"{status} Data type check: {len(mismatches)} mismatches"
        )
        
        self.checks_history.append(result)
        return result
    
    def check_value_range(
        self,
        df: DataFrame,
        column: str,
        min_value: Any = None,
        max_value: Any = None,
    ) -> Dict[str, Any]:
        """
        Check if column values are within expected range
        
        Args:
            df: DataFrame to check
            column: Column name
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        
        Returns:
            Dictionary with check results
        """
        # Get actual min/max
        stats = df.agg(
            F.min(column).alias('actual_min'),
            F.max(column).alias('actual_max'),
            F.count(F.when(F.col(column).isNull(), 1)).alias('null_count'),
        ).collect()[0]
        
        actual_min = stats['actual_min']
        actual_max = stats['actual_max']
        out_of_range = 0
        
        if min_value is not None:
            out_of_range += df.filter(F.col(column) < min_value).count()
        if max_value is not None:
            out_of_range += df.filter(F.col(column) > max_value).count()
        
        passed = out_of_range == 0
        
        result = {
            'check_type': 'value_range',
            'column': column,
            'min_expected': min_value,
            'max_expected': max_value,
            'min_actual': actual_min,
            'max_actual': actual_max,
            'out_of_range_records': out_of_range,
            'passed': passed,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        status = '✅' if passed else '⚠️'
        self.logger.info(
            f"{status} Range check '{column}': {out_of_range} out-of-range records"
        )
        
        self.checks_history.append(result)
        return result
    
    def check_completeness(
        self,
        df: DataFrame,
        required_columns: List[str],
    ) -> Dict[str, Any]:
        """
        Check if all required columns are present
        
        Args:
            df: DataFrame to check
            required_columns: List of required column names
        
        Returns:
            Dictionary with check results
        """
        available_columns = df.columns
        missing_columns = [col for col in required_columns if col not in available_columns]
        
        passed = len(missing_columns) == 0
        
        result = {
            'check_type': 'completeness',
            'required_columns': required_columns,
            'available_columns': available_columns,
            'missing_columns': missing_columns,
            'passed': passed,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        status = '✅' if passed else '❌'
        self.logger.info(
            f"{status} Completeness check: {len(missing_columns)} missing columns"
        )
        
        self.checks_history.append(result)
        return result
    
    def run_all_checks(
        self,
        df: DataFrame,
        null_checks: Dict[str, float] = None,
        key_columns: List[str] = None,
        expected_types: Dict[str, str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Run all quality checks on DataFrame
        
        Args:
            df: DataFrame to check
            null_checks: Dict of {column: threshold_percent}
            key_columns: Columns for duplicate checking
            expected_types: Expected column types
        
        Returns:
            List of all check results
        """
        results = []
        
        # Null value checks
        if null_checks:
            for column, threshold in null_checks.items():
                results.append(self.check_null_values(df, column, threshold))
        
        # Duplicate checks
        if key_columns:
            results.append(self.check_duplicates(df, key_columns))
        
        # Data type checks
        if expected_types:
            results.append(self.check_data_types(df, expected_types))
        
        # Summary
        passed_count = sum(1 for r in results if r.get('passed', False))
        total_count = len(results)
        
        self.logger.info(
            f"📊 Quality checks completed: {passed_count}/{total_count} passed"
        )
        
        return results
    
    def get_report(self) -> Dict[str, Any]:
        """Get quality check history report"""
        return {
            'total_checks': len(self.checks_history),
            'passed_checks': sum(1 for c in self.checks_history if c.get('passed', False)),
            'failed_checks': sum(1 for c in self.checks_history if not c.get('passed', False)),
            'checks': self.checks_history,
            'report_timestamp': datetime.utcnow().isoformat(),
        }
