# file: backend/agents/visualization_agent.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import uuid
from typing import List, Dict, Any
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

class VisualizationAgent:
    def __init__(self, output_dir: str = "backend/visualizations"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        # Set style
        sns.set_theme(style="whitegrid")

    def _save_plot(self, title: str) -> str:
        """Save the current plot to a file and return the path."""
        filename = f"{uuid.uuid4()}_{title.replace(' ', '_').lower()}.png"
        path = os.path.join(self.output_dir, filename)
        plt.title(title)
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        logger.info(f"Generated plot: {path}")
        return path

    def generate_correlation_heatmap(self, df: pd.DataFrame) -> str:
        """Generate correlation heatmap."""
        plt.figure(figsize=(10, 8))
        numeric_df = df.select_dtypes(include=['number'])
        if numeric_df.empty:
            return None
            
        corr = numeric_df.corr()
        sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
        return self._save_plot("Correlation Matrix")

    def generate_distribution_plots(self, df: pd.DataFrame) -> List[str]:
        """Generate distribution plots for key numeric columns."""
        paths = []
        numeric_cols = df.select_dtypes(include=['number']).columns[:3] # Limit to top 3 to avoid spam
        
        for col in numeric_cols:
            plt.figure(figsize=(8, 6))
            sns.histplot(df[col], kde=True)
            paths.append(self._save_plot(f"Distribution of {col}"))
            
        return paths

    def generate_categorical_plots(self, df: pd.DataFrame) -> List[str]:
        """Generate bar charts for categorical columns."""
        paths = []
        cat_cols = df.select_dtypes(include=['object', 'category']).columns[:3]
        
        for col in cat_cols:
            if df[col].nunique() > 20: # Skip high cardinality
                continue
                
            plt.figure(figsize=(10, 6))
            sns.countplot(y=col, data=df, order=df[col].value_counts().index)
            paths.append(self._save_plot(f"Count of {col}"))
            
        return paths

    def generate_time_series_plot(self, df: pd.DataFrame, date_col: str, value_col: str) -> str:
        """Generate a time series line chart."""
        plt.figure(figsize=(12, 6))
        
        # Ensure date column is datetime
        df_copy = df.copy()
        df_copy[date_col] = pd.to_datetime(df_copy[date_col])
        df_copy = df_copy.sort_values(by=date_col)
        
        sns.lineplot(x=date_col, y=value_col, data=df_copy)
        return self._save_plot(f"Trend of {value_col} over Time")

    def create_visualizations(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Auto-generate a suite of visualizations."""
        logger.info("Generating visualizations...")
        
        charts = {
            "correlation": [],
            "distributions": [],
            "categorical": [],
            "time_series": []
        }
        
        # Correlation
        heatmap = self.generate_correlation_heatmap(df)
        if heatmap:
            charts["correlation"].append(heatmap)
            
        # Distributions
        charts["distributions"] = self.generate_distribution_plots(df)
        
        # Categorical
        charts["categorical"] = self.generate_categorical_plots(df)
        
        # Detect potential time series
        # Simple heuristic: find a date col and a numeric col
        date_cols = []
        for col in df.columns:
            if "date" in col.lower() or "time" in col.lower():
                try:
                    pd.to_datetime(df[col])
                    date_cols.append(col)
                except:
                    pass
        
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        if date_cols and len(numeric_cols) > 0:
            # Plot first date col vs first numeric col as a sample
            ts_plot = self.generate_time_series_plot(df, date_cols[0], numeric_cols[0])
            charts["time_series"].append(ts_plot)
            
        return charts
# end file
