# AI Business Intelligence Copilot - Unified HuggingFace Spaces App
# 100% FREE - No separate backend needed!

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
import requests
from io import BytesIO

# Set page config
st.set_page_config(
    page_title="AI Business Intelligence Copilot",
    page_icon="📊",
    layout="wide"
)

# ============== LLM Configuration ==============
import os
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

def call_groq(prompt: str):
    if not GROQ_API_KEY:
        raise Exception("No Groq Key")
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )
    return response.choices[0].message.content

def call_openrouter(prompt: str):
    if not OPENROUTER_API_KEY:
        raise Exception("No OpenRouter Key")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/llama-3.1-70b-instruct:free",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    raise Exception(f"OpenRouter Error: {response.text}")

def call_huggingface(prompt: str):
    if not HUGGINGFACE_API_KEY:
        raise Exception("No HuggingFace Key")
    
    API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
    if response.status_code == 200:
        return response.json()[0]['generated_text']
    raise Exception(f"HuggingFace Error: {response.text}")

def get_llm_response(prompt: str) -> str:
    """Get response with fallback strategy: Groq -> OpenRouter -> HuggingFace."""
    errors = []
    
    # 1. Try Groq
    try:
        return call_groq(prompt)
    except Exception as e:
        errors.append(f"Groq: {str(e)}")
    
    # 2. Try OpenRouter
    try:
        return call_openrouter(prompt)
    except Exception as e:
        errors.append(f"OpenRouter: {str(e)}")
        
    # 3. Try HuggingFace
    try:
        return call_huggingface(prompt)
    except Exception as e:
        errors.append(f"HuggingFace: {str(e)}")
    
    return f"⚠️ All AI providers failed.\nErrors:\n" + "\n".join(errors)

# ============== Agent Functions ==============

def analyze_data_quality(df: pd.DataFrame) -> dict:
    """Data Quality Agent - Check for issues."""
    missing = df.isnull().sum()
    duplicates = df.duplicated().sum()
    
    quality_score = 100
    if missing.sum() > 0:
        quality_score -= min(20, (missing.sum() / len(df)) * 100)
    if duplicates > 0:
        quality_score -= min(20, (duplicates / len(df)) * 100)
    
    return {
        "quality_score": round(quality_score, 2),
        "missing_values": missing[missing > 0].to_dict(),
        "duplicates": int(duplicates),
        "total_rows": len(df),
        "total_columns": len(df.columns)
    }

def get_statistics(df: pd.DataFrame) -> dict:
    """Statistical Agent - Compute stats."""
    numeric_stats = df.describe().to_dict()
    
    # Correlations
    numeric_df = df.select_dtypes(include=['number'])
    correlations = []
    if len(numeric_df.columns) > 1:
        corr_matrix = numeric_df.corr()
        for i in range(len(corr_matrix.columns)):
            for j in range(i):
                val = corr_matrix.iloc[i, j]
                if abs(val) > 0.5:
                    correlations.append({
                        "col1": corr_matrix.columns[i],
                        "col2": corr_matrix.columns[j],
                        "value": round(val, 3)
                    })
    
    return {
        "numeric_stats": numeric_stats,
        "correlations": correlations
    }

def create_visualizations(df: pd.DataFrame) -> list:
    """Visualization Agent - Generate charts."""
    charts = []
    
    # Correlation heatmap
    numeric_df = df.select_dtypes(include=['number'])
    if len(numeric_df.columns) > 1:
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm', fmt=".2f", ax=ax)
        ax.set_title("Correlation Matrix")
        charts.append(("Correlation Matrix", fig))
    
    # Distribution plots for numeric columns
    for col in numeric_df.columns[:3]:
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.histplot(df[col], kde=True, ax=ax)
        ax.set_title(f"Distribution of {col}")
        charts.append((f"Distribution: {col}", fig))
    
    # Categorical bar charts
    cat_cols = df.select_dtypes(include=['object', 'category']).columns[:2]
    for col in cat_cols:
        if df[col].nunique() <= 15:
            fig, ax = plt.subplots(figsize=(10, 6))
            df[col].value_counts().plot(kind='bar', ax=ax)
            ax.set_title(f"Count of {col}")
            ax.set_xlabel(col)
            charts.append((f"Bar Chart: {col}", fig))
    
    return charts

def generate_sql(query: str, columns: list) -> str:
    """SQL Agent - Generate SQL from natural language."""
    prompt = f"""Convert this natural language query to SQL.
Table name: dataset
Columns: {columns}

Query: "{query}"

Return ONLY the SQL query, no explanation."""
    
    return get_llm_response(prompt)

def semantic_query(query: str, df_summary: str) -> str:
    """Semantic Query Agent - Answer questions about data."""
    prompt = f"""You are a Business Intelligence Analyst.
Answer this question based on the data summary below.

Question: "{query}"

Data Summary:
{df_summary}

Provide a clear, data-driven answer."""
    
    return get_llm_response(prompt)

# ============== UI Components ==============

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
    .metric-card {
        background: linear-gradient(145deg, #f0f2f6, #ffffff);
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🤖 AI Business Intelligence Copilot</h1>', unsafe_allow_html=True)
st.markdown("**100% Free** • Upload CSV/Excel → AI analyzes → Get insights, charts & answers")
st.markdown("---")

# Sidebar
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio("", ["📂 Upload & Analyze", "📊 Visualizations", "💬 Ask Questions", "📈 Statistics"])

# Session state
if "df" not in st.session_state:
    st.session_state.df = None
if "quality" not in st.session_state:
    st.session_state.quality = None
if "stats" not in st.session_state:
    st.session_state.stats = None
if "charts" not in st.session_state:
    st.session_state.charts = None

# ============== Pages ==============

if page == "📂 Upload & Analyze":
    st.title("📂 Upload Your Dataset")
    
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx", "xls"])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.session_state.df = df
            st.success(f"✅ Loaded **{len(df)}** rows, **{len(df.columns)}** columns")
            
            # Preview
            st.subheader("Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Analyze button
            if st.button("🚀 Run AI Analysis", type="primary"):
                with st.spinner("🤖 Agents analyzing your data..."):
                    # Quality check
                    st.session_state.quality = analyze_data_quality(df)
                    
                    # Statistics
                    st.session_state.stats = get_statistics(df)
                    
                    # Visualizations
                    st.session_state.charts = create_visualizations(df)
                    
                st.success("✅ Analysis complete! Check other tabs for results.")
                st.balloons()
            
            # Show quality results if available
            if st.session_state.quality:
                st.subheader("📋 Data Quality Report")
                q = st.session_state.quality
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Quality Score", f"{q['quality_score']}%")
                col2.metric("Total Rows", q['total_rows'])
                col3.metric("Total Columns", q['total_columns'])
                col4.metric("Duplicates", q['duplicates'])
                
                if q['missing_values']:
                    st.warning(f"⚠️ Missing values found: {q['missing_values']}")
                    
        except Exception as e:
            st.error(f"Error reading file: {e}")

elif page == "📊 Visualizations":
    st.title("📊 Generated Visualizations")
    
    if st.session_state.charts:
        for title, fig in st.session_state.charts:
            st.subheader(title)
            st.pyplot(fig)
            plt.close(fig)
    else:
        st.info("📂 Please upload a dataset and run analysis first.")

elif page == "💬 Ask Questions":
    st.title("💬 Ask Your Data")
    
    if st.session_state.df is not None:
        df = st.session_state.df
        
        query = st.text_area("Your Question", placeholder="e.g., What is the average sales by region?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Generate SQL"):
                if query:
                    with st.spinner("Generating SQL..."):
                        sql = generate_sql(query, list(df.columns))
                        st.code(sql, language="sql")
                        
                        # Try to execute if simple
                        try:
                            import sqlite3
                            conn = sqlite3.connect(":memory:")
                            df.to_sql("dataset", conn, index=False)
                            result = pd.read_sql_query(sql, conn)
                            st.dataframe(result)
                            conn.close()
                        except:
                            st.info("SQL generated. Manual execution may be needed.")
        
        with col2:
            if st.button("🧠 Semantic Answer"):
                if query:
                    with st.spinner("Thinking..."):
                        summary = df.describe().to_string() + "\n\nSample:\n" + df.head(5).to_string()
                        answer = semantic_query(query, summary)
                        st.markdown(answer)
    else:
        st.info("📂 Please upload a dataset first.")

elif page == "📈 Statistics":
    st.title("📈 Statistical Analysis")
    
    if st.session_state.stats:
        stats = st.session_state.stats
        
        # Correlations
        if stats['correlations']:
            st.subheader("🔗 Strong Correlations Found")
            for corr in stats['correlations']:
                st.write(f"• **{corr['col1']}** ↔ **{corr['col2']}**: {corr['value']}")
        
        # Numeric stats
        st.subheader("📊 Descriptive Statistics")
        if st.session_state.df is not None:
            st.dataframe(st.session_state.df.describe(), use_container_width=True)
    else:
        st.info("📂 Please upload a dataset and run analysis first.")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using LangGraph concepts • 100% Free on HuggingFace Spaces")
