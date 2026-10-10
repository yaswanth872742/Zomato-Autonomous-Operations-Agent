# Zomato Autonomous Operations Agent

An AI-powered operations planning agent that combines machine learning, tool execution, and result verification to prepare demand forecasts and rider deployment recommendations.

The project extends an existing Zomato demand forecasting and rider planning system by adding a Gemini-powered agent that interprets an operations request, calls Python tools, gathers results, verifies key planning figures, and presents an actionable report.

## Project Overview

Food delivery operations need more than a demand forecast. They need to identify high-demand localities, estimate rider requirements, assess operational risks, and prepare a practical deployment plan.

This project demonstrates how an AI agent can use an existing analytical system to complete a defined operational task instead of only answering questions using generated text.

The agent accepts a natural-language request, identifies the required analysis, invokes available tools, collects their outputs, checks the results, and generates a final report.

**Main workflow:**

User Request → Understand the Goal → Select Tools → Execute Analysis → Observe Results → Verify Output → Generate Report

The application is designed for operational planning and does not dispatch actual riders or modify live delivery operations.

## Business Problem

A city-level demand forecast alone is not sufficient for operational decision-making.

Operations teams also need to understand:

- How many orders are expected?
- Which localities should receive higher priority?
- How many active and standby riders should be planned?
- What risks or data limitations should be considered?
- Are the generated recommendations consistent with the analytical results?

The objective is to automate the preparation of this planning report while keeping the underlying calculations grounded in the existing Python backend.

## Solution Approach

The project combines a forecasting and decision-support system with an AI agent.

1. **Understand the request:** The agent receives an operational task in natural language.
2. **Plan the analysis:** It determines which available tools are required.
3. **Execute tools:** The agent calls Python functions that analyze city demand and locality-level planning data.
4. **Observe results:** It receives structured outputs containing forecasts, locality priorities, rider recommendations, and risk information.
5. **Verify the results:** Validation checks examine whether the forecast exists, locality data is sufficient, rider recommendations are valid, and locality allocation does not exceed the city forecast.
6. **Generate the report:** The agent presents the findings, operational recommendations, supporting evidence, and relevant limitations.

## Agent Architecture

The system uses a tool-based agent architecture.

**User Interface — `agent_app.py`**

Provides a Streamlit interface where users enter a request, run the agent, and review its response, verification results, and execution trace.

**Agent Logic — `agent.py`**

Manages the bounded agent loop, communicates with the Gemini model, processes tool calls, and prepares the final response.

**Tool Layer — `agent_tools.py`**

Exposes Python functions for accessing the forecasting and operational planning logic.

**Analytical Backend — `backend.py`**

Contains the existing data processing, demand forecasting, locality scoring, rider planning, and decision-support functions.

**Forecasting Model — `forecast_model.pkl`**

Stores the trained forecasting model used by the analytical backend.

### Execution Flow

```text
Natural-Language Request
          |
          v
     Gemini Model
          |
          v
   Select Available Tool
          |
          v
  Python Backend Execution
          |
          v
    Observe Tool Results
          |
          v
   Verify Planning Figures
          |
          v
     Final Report
```

## Key Features

- Natural-language requests for operational planning.
- Integration with an existing Python forecasting backend.
- Tool-based execution using structured analytical results.
- City-level demand forecasting and historical comparisons.
- Locality-level demand scoring and prioritization.
- Active rider and standby rider recommendations.
- Operational risk and data-sufficiency information.
- Verification checks for key planning figures.
- Execution trace showing tool calls and their results.
- A Streamlit interface for reviewing the final report.

## Demand Forecasting Methodology

The underlying forecasting system processes historical order data and aggregates it into daily demand.

The forecasting workflow includes:

1. Data validation and preparation.
2. Daily demand aggregation.
3. Feature engineering using lag values, rolling statistics, and calendar-related features.
4. Demand prediction using the trained XGBoost model.
5. Locality demand scoring and forecast allocation.
6. Rider planning based on predefined operational rules.

### Locality Demand Scoring

The existing system combines historical and recent locality demand:

- Historical demand: 75%
- Recent demand: 25%

This weighting helps identify localities with established demand while considering recent activity.

### Data Sufficiency

The underlying system uses a minimum threshold of 30 historical records for locality-level planning. When sufficient data is unavailable, the system should communicate the limitation rather than present an unsupported locality recommendation.

### Rider Planning

The backend estimates active and standby rider requirements using predefined planning rules. These recommendations are intended for planning purposes and are not validated real-world fleet deployment decisions.

## Result Verification

Verification is an important part of the agent workflow because a fluent AI response alone does not guarantee that the analysis is correct.

The application checks:

- Whether a forecast value exists.
- Whether locality data is sufficient.
- Whether rider recommendations are valid.
- Whether locality-level allocated orders exceed the city forecast.

The interface displays the verification status and supporting figures. These checks establish basic consistency of the results; they do not prove that the forecast is accurate or that the operational recommendations are optimal.

## Technology Stack

- **Python** — Application logic and tool execution.
- **Google Gemini API** — Natural-language understanding and agent decisions.
- **Google Gen AI SDK** — Communication with the Gemini model.
- **Pandas and NumPy** — Data processing and numerical operations.
- **XGBoost and Scikit-learn** — Forecasting and machine-learning utilities.
- **Joblib** — Loading the trained forecasting model.
- **Streamlit** — Interactive application interface.
- **python-dotenv** — Loading environment variables during local development.

## Project Structure

```text
Zomato-Autonomous-Operations-Agent/
|
├── agent.py
├── agent_app.py
├── agent_tools.py
├── app.py
├── backend.py
├── forecast_model.pkl
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
|
├── datasets/
├── notebooks/
└── screenshots/
```

The original dashboard and forecasting backend are retained, while the agent modules add the autonomous operations workflow. The dataset and supporting folders should contain the files required by the application.

## Setup and Installation

### 1. Clone the Repository

```bash
git clone <your-github-repository-url>
cd Zomato-Autonomous-Operations-Agent
```

### 2. Install Dependencies

Use Python and install the packages listed in `requirements.txt`.

```bash
python -m pip install -r requirements.txt
```

### 3. Configure the Gemini API Key

Create a `.env` file in the project root:

```text
GEMINI_API_KEY=your_gemini_api_key
```

Replace the example value with your own API key.

**Security:** Never commit `.env` or expose your API key in the source code, screenshots, or public repository. Use `.env.example` to document the required variable without including a real key.

### 4. Run the Agent Application

```bash
python -m streamlit run agent_app.py
```

Open the local URL displayed in the terminal, normally `http://localhost:8501`.

The existing dashboard can be run separately using:

```bash
python -m streamlit run app.py
```

Make sure the required dataset and trained model are available at the paths expected by the backend.

## Example Usage

A sample request is:

> Prepare a demand forecast and rider planning summary for Chennai for the next forecast date. Identify the highest-priority localities, calculate active and standby rider requirements, assess operational risks, and verify the planning figures.

The agent uses the available analytical tools to prepare the report.

The resulting report can include:

- Forecasted city-level orders.
- Historical and recent demand comparisons.
- Priority localities and their demand scores.
- Recommended active and standby riders.
- Operational risks and data limitations.
- Verification results and supporting evidence.

## Assumptions and Limitations

- The forecasting model uses historical order data rather than live order inflow.
- Demand is aggregated at the daily level, so exact hourly peak periods are unavailable.
- Locality scoring and rider planning use predefined rules and assumptions.
- Verification checks test consistency, not forecast accuracy.
- Recommendations do not account fully for live rider availability, traffic, weather, or restaurant preparation times.
- The Gemini API depends on network connectivity, model availability, and API usage limits.
- The agent operates within a bounded execution loop and the tools made available to it.
- The application prepares recommendations only; it does not perform real-world rider dispatch.

## Future Improvements

- Add more robust retries and recovery for failed tool calls.
- Expand verification with independent calculations and additional edge-case tests.
- Add human approval before any future operational action.
- Introduce persistent task state and execution history.
- Integrate real-time order and rider availability data where authorized.
- Add automated tests and structured logging.
- Deploy the application with securely managed API credentials.
- Evaluate forecast quality and agent reliability using repeatable test cases.

## Project Takeaway

This project demonstrates how an existing machine-learning application can be extended into a tool-using AI agent.

Rather than relying only on generated text, the agent calls analytical functions, uses their results to prepare operational recommendations, and checks key figures before presenting its final response.

The main focus is the complete workflow: **understanding a task, executing tools, observing results, verifying outputs, and communicating a useful decision.**

## Author

**Yaswanth Yadala**

*Zomato Autonomous Operations Agent — AI-assisted Demand Forecasting and Rider Planning*
