# file: backend/agents/forecasting_agent.py
import pandas as pd
import numpy as np
from prophet import Prophet
from typing import Dict, Any, Optional
from backend.utils.logger import setup_logger
import matplotlib.pyplot as plt
import os
import uuid

logger = setup_logger(__name__)

class ForecastingAgent:
    def __init__(self, output_dir: str = "backend/forecasting"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def detect_time_series(self, df: pd.DataFrame) -> Optional[tuple]:
        """Identify the best date column and target metric for forecasting."""
        date_col = None
        target_col = None
        
        # Find date column
        for col in df.columns:
            if "date" in col.lower() or "time" in col.lower():
                try:
                    pd.to_datetime(df[col])
                    date_col = col
                    break
                except:
                    continue
        
        # Find target column (numeric, high variance usually interesting)
        if date_col:
            numeric_cols = df.select_dtypes(include=['number']).columns
            # Prefer columns like 'sales', 'revenue', 'count'
            for col in numeric_cols:
                if any(x in col.lower() for x in ['sales', 'revenue', 'amount', 'total', 'price']):
                    target_col = col
                    break
            if not target_col and len(numeric_cols) > 0:
                target_col = numeric_cols[0]
                
        return (date_col, target_col) if date_col and target_col else None

    def run_forecast(self, df: pd.DataFrame, periods: int = 30) -> Dict[str, Any]:
        """Run Prophet forecast."""
        ts_cols = self.detect_time_series(df)
        if not ts_cols:
            logger.info("No suitable time-series columns found.")
            return {"status": "skipped", "reason": "No date/numeric pair found"}
            
        date_col, target_col = ts_cols
        logger.info(f"Forecasting {target_col} based on {date_col}")
        
        # Prepare data for Prophet
        prophet_df = df[[date_col, target_col]].rename(columns={date_col: 'ds', target_col: 'y'})
        prophet_df['ds'] = pd.to_datetime(prophet_df['ds'])
        
        # Aggregate duplicates (Prophet doesn't like duplicate dates)
        prophet_df = prophet_df.groupby('ds').sum().reset_index()
        
        try:
            m = Prophet()
            m.fit(prophet_df)
            
            future = m.make_future_dataframe(periods=periods)
            forecast = m.predict(future)
            
            # Plotting
            fig1 = m.plot(forecast)
            plot_path = os.path.join(self.output_dir, f"{uuid.uuid4()}_forecast.png")
            fig1.savefig(plot_path)
            plt.close(fig1)
            
            fig2 = m.plot_components(forecast)
            components_path = os.path.join(self.output_dir, f"{uuid.uuid4()}_components.png")
            fig2.savefig(components_path)
            plt.close(fig2)
            
            # Calculate simple error metrics (on training set for now as proxy)
            # In production, we'd do a train/test split
            return {
                "status": "success",
                "target_column": target_col,
                "forecast_plot": plot_path,
                "components_plot": components_path,
                "forecast_data": forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods).to_dict(orient='records')
            }
            
        except Exception as e:
            logger.error(f"Forecasting failed: {e}")
            return {"status": "failed", "error": str(e)}
# end file
