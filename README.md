# AI Business Intelligence Copilot

A fully production-ready AI Business Intelligence Copilot, using free and open-source tools, with multi-agent reasoning, semantic querying, SQL generation, data analysis, forecasting, charts, PDF reports, evaluation, observability, and full-stack deployment.

## 📂 Folder Structure

```
ai-bi-copilot/
│── backend/
│   ├── main.py
│   ├── agents/
│   │   ├── data_interpreter.py
│   │   ├── statistical_agent.py
│   │   ├── visualization_agent.py
│   │   ├── forecasting_agent.py
│   │   ├── report_writer.py
│   │   ├── sql_agent.py
│   │   ├── semantic_query_agent.py
│   │   └── data_quality_agent.py
│   ├── graph/
│   │   └── workflow.py
│   ├── analysis/
│   ├── visualizations/
│   ├── forecasting/
│   ├── report/
│   ├── sql/
│   ├── semantic_query/
│   ├── data_quality/
│   └── utils/
│
│── frontend/
│   └── app.py
│
│── tests/
│── docker/
│── requirements.txt
│── README.md
│── docker-compose.yml
```

## 🏗 Architecture Diagrams

### 1. System Architecture

```mermaid
graph TB
    subgraph Frontend [Streamlit Frontend]
        UI[User Interface]
        Upload[Dataset Upload]
        Dash[Dashboards]
    end

    subgraph Backend [FastAPI Backend]
        API[API Gateway]
        Orch[LangGraph Orchestrator]
        
        subgraph Agents [Agent Swarm]
            DI[Data Interpreter]
            SA[Statistical Analysis]
            VA[Visualization]
            FA[Forecasting]
            RW[Report Writer]
            SQL[SQL Agent]
            SQ[Semantic Query]
            DQ[Data Quality]
        end
        
        DB[(SQLite)]
        VecDB[(ChromaDB)]
    end

    UI --> API
    API --> Orch
    Orch --> Agents
    Agents --> DB
    Agents --> VecDB
```

### 2. Multi-Agent Workflow

```mermaid
stateDiagram-v2
    [*] --> Supervisor
    Supervisor --> DataInterpreter: New Dataset
    DataInterpreter --> DataQuality: Validate
    DataQuality --> StatisticalAnalysis: Clean Data
    StatisticalAnalysis --> Visualization: Generate Plots
    StatisticalAnalysis --> Forecasting: Time Series?
    Visualization --> ReportWriter: Charts Ready
    Forecasting --> ReportWriter: Forecasts Ready
    ReportWriter --> [*]: PDF Generated
    
    Supervisor --> SQLAgent: User SQL Query
    Supervisor --> SemanticQuery: User Question
```

### 3. Data Flow

```mermaid
sequenceDiagram
    participant User
    participant Streamlit
    participant FastAPI
    participant Supervisor
    participant Agents
    participant Storage

    User->>Streamlit: Upload CSV
    Streamlit->>FastAPI: POST /analyze_dataset
    FastAPI->>Supervisor: Start Workflow
    Supervisor->>Agents: Dispatch Tasks
    Agents->>Storage: Save Intermediate Results (SQLite/Chroma)
    Agents->>Supervisor: Task Complete
    Supervisor->>FastAPI: Workflow Complete
    FastAPI->>Streamlit: Return Results
    Streamlit->>User: Display Dashboard
```

### 4. Component Diagram

```mermaid
classDiagram
    class Frontend {
        +StreamlitApp
        +render_dashboard()
        +handle_upload()
    }

    class Backend {
        +FastAPI
        +endpoints
    }

    class Supervisor {
        +LangGraph
        +route_task()
    }

    class Agent {
        <<interface>>
        +process()
        +get_tools()
    }

    class DataInterpreter {
        +infer_schema()
    }
    
    class SQLAgent {
        +text_to_sql()
    }

    Frontend --> Backend
    Backend --> Supervisor
    Supervisor --> Agent
    Agent <|-- DataInterpreter
    Agent <|-- SQLAgent
```

## 🚀 Deployment

### Prerequisites
- Docker & Docker Compose
- API Keys (Groq, OpenRouter, HuggingFace)

### Running Locally
1. Clone the repository
2. Create a `.env` file with your API keys
3. Run `docker-compose up --build`
4. Access Frontend at `http://localhost:8501`
5. Access Backend Docs at `http://localhost:8000/docs`
