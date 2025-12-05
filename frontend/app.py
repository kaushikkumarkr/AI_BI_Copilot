# file: frontend/app.py
import streamlit as st
import requests
import pandas as pd
import json
import time
import os

# Config
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="AI Business Intelligence Copilot",
    page_icon="📊",
    layout="wide"
)

# Sidebar
st.sidebar.title("🤖 AI BI Copilot")
page = st.sidebar.radio("Navigation", ["Upload Dataset", "Dashboard", "Query Data", "Reports"])

if page == "Upload Dataset":
    st.title("📂 Upload Dataset")
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])
    
    if uploaded_file:
        if st.button("Start Analysis"):
            with st.spinner("Uploading and starting agents..."):
                files = {"file": uploaded_file}
                try:
                    res = requests.post(f"{API_URL}/analyze_dataset", files=files)
                    if res.status_code == 200:
                        task_id = res.json()["task_id"]
                        st.session_state["task_id"] = task_id
                        st.success(f"Analysis started! Task ID: {task_id}")
                        st.info("Go to the 'Dashboard' page to view progress.")
                    else:
                        st.error("Upload failed.")
                except Exception as e:
                    st.error(f"Connection error: {e}")

elif page == "Dashboard":
    st.title("📊 Insights Dashboard")
    
    if "task_id" not in st.session_state:
        st.warning("Please upload a dataset first.")
    else:
        task_id = st.session_state["task_id"]
        st.write(f"**Task ID:** {task_id}")
        
        # Poll for status (Mock for now, real implementation would hit status endpoint)
        # In a real app, we'd fetch the JSON results from the backend
        # For this demo, we assume the backend saves results to files we can serve or the API returns them
        
        st.info("Analysis is running in the background... (Check backend logs for real-time updates)")
        
        # Placeholder for tabs
        tab1, tab2, tab3 = st.tabs(["Overview", "Visualizations", "Forecasts"])
        
        with tab1:
            st.header("Dataset Overview")
            st.write("Waiting for Data Interpreter...")
            
        with tab2:
            st.header("Generated Charts")
            st.write("Waiting for Visualization Agent...")
            
        with tab3:
            st.header("Forecasting")
            st.write("Waiting for Forecasting Agent...")

elif page == "Query Data":
    st.title("💬 Ask Your Data")
    
    query = st.text_input("Ask a question (e.g., 'Show total revenue by region')")
    
    if st.button("Submit"):
        if query:
            # Determine if SQL or Semantic
            if any(x in query.lower() for x in ["show", "list", "count", "sum", "average"]):
                endpoint = "sql_query"
            else:
                endpoint = "semantic_query"
                
            with st.spinner("Thinking..."):
                try:
                    payload = {"query": query, "dataset_id": st.session_state.get("task_id", "demo")}
                    res = requests.post(f"{API_URL}/{endpoint}", json=payload)
                    st.json(res.json())
                except Exception as e:
                    st.error(f"Error: {e}")

elif page == "Reports":
    st.title("📑 Reports")
    
    if "task_id" in st.session_state:
        task_id = st.session_state["task_id"]
        if st.button("Download PDF Report"):
            st.write(f"Downloading report for {task_id}...")
            # Link to backend download
            st.markdown(f"[Click here to download]({API_URL}/report/{task_id})")
    else:
        st.warning("No analysis found.")
# end file
