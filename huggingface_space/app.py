# HuggingFace Space Streamlit App
import streamlit as st
import requests
import pandas as pd

# ⚠️ UPDATE THIS TO YOUR RENDER BACKEND URL
API_URL = "https://ai-bi-copilot-api.onrender.com"  # Replace with your actual Render URL

st.set_page_config(
    page_title="AI Business Intelligence Copilot",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem;
    }
    .feature-card {
        background: linear-gradient(145deg, #1e1e2e, #2d2d44);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem;
        border: 1px solid #3d3d5c;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🤖 AI Business Intelligence Copilot</h1>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("", ["🏠 Home", "📂 Upload Dataset", "💬 Query Data", "📑 Reports"])

if page == "🏠 Home":
    st.markdown("### Welcome to the AI BI Copilot!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 📊 Auto Analysis
        Upload any CSV/Excel and watch AI agents:
        - Analyze data quality
        - Generate statistics
        - Create visualizations
        """)
    
    with col2:
        st.markdown("""
        #### 📈 Forecasting
        Time-series detection with:
        - Prophet forecasting
        - Trend decomposition
        - Error metrics
        """)
    
    with col3:
        st.markdown("""
        #### 💬 Ask Questions
        Natural language queries:
        - SQL generation
        - Semantic answers
        - Data insights
        """)

elif page == "📂 Upload Dataset":
    st.title("📂 Upload Your Dataset")
    
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])
    
    if uploaded_file:
        # Preview
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ Loaded {len(df)} rows, {len(df.columns)} columns")
            st.dataframe(df.head(10))
            
            if st.button("🚀 Start AI Analysis", type="primary"):
                with st.spinner("Uploading and starting agents..."):
                    uploaded_file.seek(0)
                    files = {"file": uploaded_file}
                    try:
                        res = requests.post(f"{API_URL}/analyze_dataset", files=files, timeout=30)
                        if res.status_code == 200:
                            task_id = res.json()["task_id"]
                            st.session_state["task_id"] = task_id
                            st.success(f"🎉 Analysis started! Task ID: `{task_id}`")
                            st.info("The AI agents are now processing your data. This may take a few minutes.")
                        else:
                            st.error(f"Upload failed: {res.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("⚠️ Backend not reachable. Make sure the API is deployed.")
                    except Exception as e:
                        st.error(f"Error: {e}")
        except Exception as e:
            st.error(f"Could not read file: {e}")

elif page == "💬 Query Data":
    st.title("💬 Ask Your Data")
    
    task_id = st.session_state.get("task_id", "")
    task_id_input = st.text_input("Task ID (from upload)", value=task_id)
    
    query = st.text_area("Your Question", placeholder="e.g., What is the total sales by region?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 SQL Query"):
            if query and task_id_input:
                with st.spinner("Generating SQL..."):
                    try:
                        res = requests.post(
                            f"{API_URL}/sql_query",
                            json={"query": query, "dataset_id": task_id_input},
                            timeout=60
                        )
                        data = res.json()
                        st.code(data.get("sql", ""), language="sql")
                        if "result" in data:
                            st.dataframe(pd.DataFrame(data["result"]))
                    except Exception as e:
                        st.error(f"Error: {e}")
    
    with col2:
        if st.button("🧠 Semantic Query"):
            if query and task_id_input:
                with st.spinner("Thinking..."):
                    try:
                        res = requests.post(
                            f"{API_URL}/semantic_query",
                            json={"query": query, "context_id": task_id_input},
                            timeout=60
                        )
                        data = res.json()
                        st.markdown(data.get("answer", "No answer"))
                    except Exception as e:
                        st.error(f"Error: {e}")

elif page == "📑 Reports":
    st.title("📑 Generated Reports")
    
    task_id = st.session_state.get("task_id", "")
    task_id_input = st.text_input("Task ID", value=task_id)
    
    if task_id_input:
        st.markdown(f"### Report for Task: `{task_id_input}`")
        st.markdown(f"[📥 Download PDF Report]({API_URL}/report/{task_id_input})")
        st.markdown(f"[📊 View Charts]({API_URL}/charts/{task_id_input})")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using LangGraph, FastAPI, and Streamlit")
