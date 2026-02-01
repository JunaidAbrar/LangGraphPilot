## 🎥 Project Demo

[![Watch the demo](https://img.youtube.com/vi/YOUTUBE_VIDEO_ID/0.jpg)](https://youtu.be/cBoaa8jBBKI)



# LangGraph Pilot #insightfactoryai #cadet_challenge
*A dataset-agnostic SQL agent that navigates natural language queries with precision*
# 🤖 Delivery Cadet Challenge: AI Data Agent

## 🏆 Executive Summary
This is a production-grade, local AI Data Agent designed to bridge the gap between static data analysis scripts and autonomous business intelligence. 

Unlike standard "Text-to-SQL" demos, this agent features a **Self-Healing Reasoning Loop** (LangGraph), **Dynamic Data Ingestion** (Excel/CSV), and **Enterprise Observability** (LangSmith). It is architected to run locally for maximum performance while leveraging state-of-the-art LLMs (Llama 3.3 70B via Groq) for reasoning.

---

## 🏗️ Architecture & Tech Stack

### The Core Stack
* **Orchestration:** [LangGraph](https://langchain-ai.github.io/langgraph/) (State Machine) - Manages the cyclic workflow of generation, validation, and repair.
* **Reasoning Engine:** **Llama 3.3 70B** (via [Groq](https://groq.com/)) - Chosen for its sub-second inference speed, essential for interactive data exploration.
* **Data Layer:** **SQLite** (Local) + **SQLAlchemy** - Provides a persistent, relational backend that outperforms in-memory Pandas for complex JOINs.
* **Frontend:** **Streamlit** + **Plotly** - A reactive UI with adaptive visualization rendering.
* **Observability:** **LangSmith** - Full trace logging for debugging and audit trails.

### The "Brain" (State Machine)
The agent follows a deterministic control flow:
1.  **Ingest:** Heuristically detects Foreign Keys (e.g., `client_id` -> `clients`) to build a knowledge graph of the data.
2.  **Plan:** User query is analyzed against the schema.
3.  **Generate:** SQL is drafted.
4.  **Validate:** Middleware checks for malicious keywords (`DROP`, `DELETE`) and syntax errors.
5.  **Repair (The Safety Net):** If execution fails, the error is fed back to the LLM. It self-corrects and retries (up to 3 times).
6.  **Visualize:** The agent autonomously decides between Bar, Pie, or Line charts based on the data topology.

---

## 🌟 Key Differentiators

| Feature | Standard Submission | This Agent |
| :--- | :--- | :--- |
| **Data Source** | Hardcoded CSV path | **Dynamic Excel/CSV Ingestion** (Drag & Drop support) |
| **Error Handling** | Crashes on bad SQL | **Self-Healing Repair Loop** (Auto-fixes syntax) |
| **Visualization** | Static Image / None | **Interactive Plotly Charts** (Smart Type Selection) |
| **Security** | None | **PII Redaction** (Regex masks Emails/Phones) |
| **Transparency** | Black Box | **LangSmith Tracing** (Full audit logs) |

---

## 🚀 Setup & Installation

### 1. Clone & Environment
```bash
git clone https://github.com/<YOUR USERNAME>/LangGraphPilot


# Create Virtual Environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\Activate

# Install Dependencies
pip install -r requirements.txt

# Load Data
Place your .csv or .xlsx files in the data/ folder. (The agent will automatically ingest them on startup or via the "Reload" button in the UI). 

# Run the Application
cd delivery-cadet-challenge
streamlit run ui/app.py
