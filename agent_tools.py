
import pandas as pd

from backend import (
    model,
    get_cities,
    create_city_dataset,
    create_daily_dataset,
    build_locality_demand_scores,
    get_forecast_results,
    run_decision_support,
)


def get_city_options():
    """Return cities available in the existing dataset."""
    return get_cities()


def analyze_city(city_name):
    """Forecast city demand and create a plan for its top locality."""

    if city_name not in get_cities():
        return {
            "status": "error",
            "message": "City not found in the available dataset.",
        }

    try:
        city_data = create_city_dataset(city_name)

        if city_data.empty:
            return {
                "status": "error",
                "message": "No historical data is available for this city.",
            }

        city_daily = create_daily_dataset(city_data)

        if len(city_daily) < 30:
            return {
                "status": "error",
                "message": "At least 30 daily observations are required.",
            }

        forecast_orders, summary = get_forecast_results(
            model, city_daily
        )

        locality_scores = build_locality_demand_scores(city_data)

        if locality_scores.empty:
            return {
                "status": "error",
                "message": (
                    "No localities meet the minimum historical-data "
                    "requirement of 30 records."
                ),
                "forecast_orders": int(forecast_orders),
                "summary": summary,
            }

        locality_scores = locality_scores.sort_values(
            "demand_score", ascending=False
        )

        top_locality = str(
            locality_scores.iloc[0]["locality"]
        )

        decision = run_decision_support(
            city_name,
            top_locality,
            forecast_orders,
            locality_scores,
            city_daily,
        )

        return {
            "status": "success",
            "city": city_name,
            "forecast_orders": int(forecast_orders),
            "summary": summary,
            "top_locality": top_locality,
            "decision_support": decision,
            "locality_scores": locality_scores.to_dict(
                orient="records"
            ),
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": f"{type(exc).__name__}: {exc}",
        }
