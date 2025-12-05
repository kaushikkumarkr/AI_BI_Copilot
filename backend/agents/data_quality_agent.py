# file: backend/agents/data_quality_agent.py
import pandas as pd
from typing import Dict, Any, List
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

class DataQualityAgent:
    def __init__(self):
        pass

    def check_missing_values(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect missing values and calculate percentage."""
        missing = df.isnull().sum()
        missing_pct = (missing / len(df)) * 100
        
        return {
            "total_missing": int(missing.sum()),
            "by_column": missing[missing > 0].to_dict(),
            "percentage": missing_pct[missing_pct > 0].to_dict()
        }

    def check_duplicates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect duplicate rows."""
        duplicates = df.duplicated().sum()
        return {
            "count": int(duplicates),
            "percentage": float((duplicates / len(df)) * 100)
        }

    def check_inconsistencies(self, df: pd.DataFrame) -> List[str]:
        """Check for common data inconsistencies."""
        issues = []
        
        # Check for mixed types in object columns (heuristic)
        for col in df.select_dtypes(include=['object']):
            if df[col].apply(type).nunique() > 1:
                issues.append(f"Column '{col}' contains mixed data types.")
                
        # Check for negative values in likely positive columns (price, quantity)
        numeric_cols = df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            if "price" in col.lower() or "cost" in col.lower() or "qty" in col.lower():
                if (df[col] < 0).any():
                    issues.append(f"Column '{col}' has negative values which might be invalid.")
                    
        return issues

    def analyze_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run full quality check."""
        logger.info("Running Data Quality Analysis...")
        
        missing = self.check_missing_values(df)
        duplicates = self.check_duplicates(df)
        inconsistencies = self.check_inconsistencies(df)
        
        # Calculate a simple quality score (0-100)
        # Deduct points for missing values and duplicates
        score = 100
        if missing['total_missing'] > 0:
            score -= min(20, missing['total_missing'] / len(df) * 100)
        if duplicates['count'] > 0:
            score -= min(20, duplicates['count'] / len(df) * 100)
        if inconsistencies:
            score -= len(inconsistencies) * 5
            
        return {
            "quality_score": max(0, round(score, 2)),
            "missing_values": missing,
            "duplicates": duplicates,
            "inconsistencies": inconsistencies,
            "is_clean": score > 90
        }
# end file
