# file: backend/agents/statistical_agent.py
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

class StatisticalAgent:
    def __init__(self):
        pass

    def get_descriptive_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get standard descriptive statistics."""
        # Numeric stats
        numeric_stats = df.describe().to_dict()
        
        # Categorical stats
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        categorical_stats = {}
        for col in categorical_cols:
            categorical_stats[col] = {
                "unique_count": int(df[col].nunique()),
                "top_value": str(df[col].mode().iloc[0]) if not df[col].mode().empty else None,
                "top_freq": int(df[col].value_counts().iloc[0]) if not df[col].value_counts().empty else 0
            }
            
        return {
            "numeric": numeric_stats,
            "categorical": categorical_stats
        }

    def get_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate correlation matrix for numeric columns."""
        numeric_df = df.select_dtypes(include=['number'])
        if numeric_df.empty:
            return {"message": "No numeric columns for correlation."}
            
        corr_matrix = numeric_df.corr()
        
        # Find strong correlations
        strong_corrs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i):
                val = corr_matrix.iloc[i, j]
                if abs(val) > 0.7:
                    strong_corrs.append({
                        "col1": corr_matrix.columns[i],
                        "col2": corr_matrix.columns[j],
                        "correlation": round(val, 3)
                    })
                    
        return {
            "matrix": corr_matrix.to_dict(),
            "strong_correlations": strong_corrs
        }

    def detect_outliers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect outliers using IQR method."""
        outliers = {}
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outlier_count = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            if outlier_count > 0:
                outliers[col] = {
                    "count": int(outlier_count),
                    "percentage": round((outlier_count / len(df)) * 100, 2),
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound)
                }
                
        return outliers

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run full statistical analysis."""
        logger.info("Running Statistical Analysis...")
        
        return {
            "descriptive_stats": self.get_descriptive_stats(df),
            "correlations": self.get_correlations(df),
            "outliers": self.detect_outliers(df)
        }
# end file
