# file: backend/graph/workflow.py
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
import pandas as pd

# Import Agents
from backend.agents.data_interpreter import DataInterpreter
from backend.agents.data_quality_agent import DataQualityAgent
from backend.agents.statistical_agent import StatisticalAgent
from backend.agents.visualization_agent import VisualizationAgent
from backend.agents.forecasting_agent import ForecastingAgent
from backend.agents.report_writer import ReportWriterAgent

# Define State
class AgentState(TypedDict):
    file_path: str
    task_id: str
    df: Any # pandas DataFrame (not serializable in standard JSON, but okay for in-memory graph)
    summary: Dict[str, Any]
    quality_report: Dict[str, Any]
    statistics: Dict[str, Any]
    visualizations: Dict[str, Any]
    forecast: Dict[str, Any]
    final_report: Dict[str, Any]

# Initialize Agents
interpreter = DataInterpreter()
quality_agent = DataQualityAgent()
stat_agent = StatisticalAgent()
viz_agent = VisualizationAgent()
forecast_agent = ForecastingAgent()
report_agent = ReportWriterAgent()

# Define Nodes
async def node_interpret(state: AgentState):
    print("--- Node: Interpret Data ---")
    result = interpreter.process(state["file_path"])
    return {"df": result["df"], "summary": result["initial_summary"]}

async def node_quality(state: AgentState):
    print("--- Node: Check Quality ---")
    report = quality_agent.analyze_quality(state["df"])
    return {"quality_report": report}

async def node_statistics(state: AgentState):
    print("--- Node: Statistics ---")
    stats = stat_agent.analyze(state["df"])
    return {"statistics": stats}

async def node_visualization(state: AgentState):
    print("--- Node: Visualization ---")
    charts = viz_agent.create_visualizations(state["df"])
    return {"visualizations": charts}

async def node_forecast(state: AgentState):
    print("--- Node: Forecasting ---")
    forecast = forecast_agent.run_forecast(state["df"])
    return {"forecast": forecast}

async def node_report(state: AgentState):
    print("--- Node: Report Generation ---")
    # Compile all results
    analysis_results = {
        "summary": state["summary"],
        "data_quality": state["quality_report"],
        "statistical_analysis": state["statistics"],
        "visualizations": state["visualizations"],
        "forecast": state["forecast"]
    }
    report = await report_agent.generate_report(state["task_id"], analysis_results)
    return {"final_report": report}

# Build Graph
workflow = StateGraph(AgentState)

workflow.add_node("interpret", node_interpret)
workflow.add_node("quality", node_quality)
workflow.add_node("statistics", node_statistics)
workflow.add_node("visualization", node_visualization)
workflow.add_node("forecast", node_forecast)
workflow.add_node("report", node_report)

# Define Edges (Sequential for now, could be parallel)
workflow.set_entry_point("interpret")
workflow.add_edge("interpret", "quality")
workflow.add_edge("quality", "statistics")
workflow.add_edge("statistics", "visualization")
workflow.add_edge("visualization", "forecast")
workflow.add_edge("forecast", "report")
workflow.add_edge("report", END)

# Compile
app_workflow = workflow.compile()
# end file
