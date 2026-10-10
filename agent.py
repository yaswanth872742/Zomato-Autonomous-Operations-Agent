
import json
import os
import pandas as pd
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from agent_tools import get_city_options, analyze_city

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. Check your .env file."
    )

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.8-flash"

SYSTEM_INSTRUCTION = """
You are a Zomato operations planning agent.

Your job is to prepare demand forecasts and rider deployment plans.

Rules:
1. Use the available Python tools to obtain real results.
2. Never invent forecasts, localities, or rider numbers.
3. Clearly report insufficient data or tool errors.
4. Distinguish actual tool results from your recommendations.
5. Explain the evidence behind your final plan.
6. Do not claim that riders were actually deployed. You only prepare plans.
7. If the user names a city and requests a forecast or rider plan, call analyze_city directly.
8. Call get_city_options only when the user asks which cities are available or does not specify a city.
"""

TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="get_city_options",
                description="Get the cities available in the dataset.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={},
                ),
            ),
            types.FunctionDeclaration(
                name="analyze_city",
                description=(
                    "Forecast tomorrow's demand for a city and "
                    "prepare an operational plan for its top eligible "
                    "locality. Use this for city-level planning requests."
                ),
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "city_name": types.Schema(
                            type="STRING",
                            description="City name exactly as listed in the dataset.",
                        )
                    },
                    required=["city_name"],
                ),
            ),
        ]
    )
]


def make_json_safe(value):
    """Convert Pandas and NumPy values into JSON-compatible data."""
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")

    if isinstance(value, pd.Series):
        return value.to_dict()

    if isinstance(value, dict):
        return {str(k): make_json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [make_json_safe(v) for v in value]

    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, TypeError):
            pass

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value


def execute_tool(name, arguments):
    """Execute only explicitly allowed local Python functions."""

    if name == "get_city_options":
        result = {
            "status": "success",
            "cities": get_city_options(),
        }

    elif name == "analyze_city":
        city_name = arguments.get("city_name", "")

        if not isinstance(city_name, str) or not city_name.strip():
            return {
                "status": "error",
                "message": "A valid city name is required.",
            }

        result = analyze_city(city_name.strip())

    else:
        return {
            "status": "error",
            "message": f"Unknown tool: {name}",
        }

    return make_json_safe(result)



def run_agent(user_request, max_steps=5):
    """Run a bounded agent loop and return an execution trace."""

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_request)],
        )
    ]

    trace = []

    for step in range(max_steps):
        print(f"Agent step {step + 1}/{max_steps}...")
        
        response = None

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        tools=TOOLS,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(
                            disable=True
                        ),
                        temperature=0.2,
                    ),
                )
                break

            except Exception as exc:
                error_text = str(exc)

                temporary_error = any(
                    marker in error_text
                    for marker in ("503", "429", "500", "UNAVAILABLE")
                )

                if not temporary_error or attempt == 2:
                    raise

                time.sleep(2 ** attempt)


        if not response.candidates:
            trace.append({
                "step": step + 1,
                "event": "error",
                "details": "Gemini returned no candidate response.",
            })
            break

        candidate = response.candidates[0]
        contents.append(candidate.content)

        function_calls = [
            part.function_call
            for part in (candidate.content.parts or [])
            if part.function_call is not None
        ]

        if not function_calls:
            return {
                "status": "completed",
                "answer": response.text or "No final answer was returned.",
                "trace": trace,
            }

        for function_call in function_calls:
            name = function_call.name
            arguments = dict(function_call.args or {})

            trace.append({
                "step": step + 1,
                "event": "tool_call",
                "tool": name,
                "arguments": arguments,
            })

            try:
                result = execute_tool(name, arguments)
            except Exception as exc:
                result = {
                    "status": "error",
                    "message": f"{type(exc).__name__}: {exc}",
                }

            trace.append({
                "step": step + 1,
                "event": "tool_result",
                "tool": name,
                "result": result,
            })

            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_function_response(
                            name=name,
                            response={"result": result},
                        )
                    ],
                )
            )

    return {
        "status": "needs_review",
        "answer": (
            "The agent reached its step limit or could not complete "
            "the request. Review the execution trace before using the plan."
        ),
        "trace": trace,
    }


def verify_plan(result):
    """Check the backend results before presenting a plan."""

    checks = []

    if result.get("status") != "success":
        return {
            "verified": False,
            "checks": [
                {
                    "check": "Tool execution",
                    "passed": False,
                    "details": result.get("message", "Tool failed."),
                }
            ],
        }

    decision = result.get("decision_support", {})
    forecast = result.get("forecast_orders")
    locality = decision.get("selected_locality", {})
    allocation = decision.get("allocation", [])

    checks.append({
        "check": "Forecast exists",
        "passed": isinstance(forecast, (int, float)) and forecast >= 0,
        "details": f"Forecast orders: {forecast}",
    })

    checks.append({
        "check": "Locality data is sufficient",
        "passed": decision.get("data_status") == "Sufficient",
        "details": f"Data status: {decision.get('data_status')}",
    })

    recommended = locality.get("recommended_riders")
    standby = locality.get("standby_riders")

    checks.append({
        "check": "Rider recommendations are valid",
        "passed": (
            isinstance(recommended, int)
            and isinstance(standby, int)
            and recommended >= 0
            and standby >= 0
        ),
        "details": (
            f"Recommended riders: {recommended}; "
            f"standby riders: {standby}"
        ),
    })

    allocation_total = sum(
        row.get("forecast_orders", 0)
        for row in allocation
        if isinstance(row, dict)
    )

    checks.append({
        "check": "Locality allocation does not exceed city forecast",
        "passed": (
            isinstance(forecast, (int, float))
            and allocation_total <= forecast
        ),
        "details": (
            f"Allocated orders: {allocation_total}; "
            f"city forecast: {forecast}"
        ),
    })

    return {
        "verified": all(check["passed"] for check in checks),
        "checks": checks,
    }
