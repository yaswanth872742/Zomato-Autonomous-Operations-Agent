
import streamlit as st

from agent import run_agent, verify_plan

st.set_page_config(
    page_title="Zomato Autonomous Operations Agent",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Zomato Autonomous Operations Agent")
st.caption(
    "AI-assisted demand forecasting and rider planning "
    "using your existing Python backend."
)

st.info(
    "The agent prepares recommendations only. "
    "It does not dispatch riders or change live operations."
)

if "agent_history" not in st.session_state:
    st.session_state.agent_history = []

request = st.text_area(
    "What should the operations agent do?",
    value=(
        "Prepare a demand forecast and rider planning summary "
        "for Agra for the next forecast date."
    ),
    height=100,
)

if st.button("Run Operations Agent", type="primary"):
    if not request.strip():
        st.warning("Enter a task before running the agent.")
    else:
        with st.spinner("Agent is planning and executing tools..."):
            try:
                result = run_agent(request)

                verification = None
                for event in result.get("trace", []):
                    if (
                        event.get("event") == "tool_result"
                        and event.get("tool") == "analyze_city"
                    ):
                        tool_result = event.get("result", {})
                        if tool_result.get("status") == "success":
                            verification = verify_plan(tool_result)
                            break

                st.session_state.agent_history = [{
                    "request": request,
                    "result": result,
                    "verification": verification,
                }]

            except Exception as exc:
                st.error(
                    f"Agent run failed: {type(exc).__name__}: {exc}"
                )

for item in reversed(st.session_state.agent_history):
    st.divider()
    st.subheader("Agent response")
    
    st.markdown(item["result"].get("answer", "No answer returned."))

    # Show key figures directly from the backend tool result.
    tool_result = next(
        (
            event.get("result", {})
            for event in item["result"].get("trace", [])
            if event.get("event") == "tool_result"
            and event.get("tool") == "analyze_city"
        ),
        None,
    )

    if tool_result and tool_result.get("status") == "success":
        decision = tool_result.get("decision_support", {})
        locality = decision.get("selected_locality", {})

        st.subheader("Verified planning figures")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Forecast orders",
            tool_result.get("forecast_orders", "N/A"),
        )
        col2.metric(
            "Top locality",
            tool_result.get("top_locality", "N/A"),
        )
        col3.metric(
            "Recommended riders",
            locality.get("recommended_riders", "N/A"),
        )
        col4.metric(
            "Standby riders",
            locality.get("standby_riders", "N/A"),
        )

        st.caption(
            "Figures are taken directly from the Python backend. "
            "Verification checks indicate consistency, not forecast accuracy."
        )


    st.subheader("Execution status")
    st.write(item["result"].get("status", "unknown"))

    st.subheader("Verification")
    verification = item["verification"]

    if verification is None:
        st.warning("No successful tool result was available to verify.")
    else:
        if verification["verified"]:
            st.success("All verification checks passed.")
        else:
            st.warning("One or more verification checks failed.")

        for check in verification["checks"]:
            icon = "✅" if check["passed"] else "❌"
            st.write(f"{icon} **{check['check']}** — {check['details']}")

    with st.expander("Execution trace"):
        st.json(item["result"].get("trace", []))
