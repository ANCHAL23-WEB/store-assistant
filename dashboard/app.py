@"
"""Streamlit analytics dashboard for the retail store assistant."""

from datetime import datetime
from typing import Any

import matplotlib.pyplot as plt

import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


@st.cache_data(ttl=60)
def fetch_dashboard_data(path: str) -> list[dict[str, Any]] | None:
    """Fetch one dashboard dataset, returning None when the API is unavailable."""
    try:
        response = requests.get(f"{API_BASE_URL}{path}", timeout=10)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("Dashboard endpoint returned an unexpected response.")
        return payload
    except (requests.RequestException, ValueError) as error:
        st.error(f"Could not load {path}: {error}")
        return None


def show_top_products(products: list[dict[str, Any]] | None) -> None:
    st.header("Top Products")
    if not products:
        st.info("No data yet")
        return

    labels = [f"{item['name']} ({item['brand']})" for item in products][::-1]
    counts = [item["search_count"] for item in products][::-1]
    figure, axis = plt.subplots()
    axis.barh(labels, counts, color="#1d4ed8")
    axis.set_xlabel("Searches")
    axis.set_ylabel("Product")
    figure.tight_layout()
    st.pyplot(figure, use_container_width=True)
    plt.close(figure)


def show_input_breakdown(breakdown: list[dict[str, Any]] | None) -> None:
    st.header("Input Method Breakdown")
    if not breakdown:
        st.info("No data yet")
        return

    figure, axis = plt.subplots()
    axis.pie(
        [item["count"] for item in breakdown],
        labels=[item["input_type"].title() for item in breakdown],
        autopct="%1.0f%%",
        startangle=90,
    )
    axis.axis("equal")
    st.pyplot(figure, use_container_width=True)
    plt.close(figure)


def show_searches_over_time(searches: list[dict[str, Any]] | None) -> None:
    st.header("Searches Over Time")
    if not searches:
        st.info("No data yet")
        return

    figure, axis = plt.subplots()
    axis.plot(
        [item["date"] for item in searches],
        [item["count"] for item in searches],
        color="#1d4ed8",
        marker="o",
    )
    axis.set_xlabel("Date")
    axis.set_ylabel("Searches")
    axis.tick_params(axis="x", rotation=45)
    figure.tight_layout()
    st.pyplot(figure, use_container_width=True)
    plt.close(figure)


def show_zero_result_searches(searches: list[dict[str, Any]] | None) -> None:
    st.header("Zero-Result Searches")
    if not searches:
        st.info("No data yet")
        return

    st.dataframe(
        searches,
        column_order=["query_text", "input_type", "timestamp"],
        hide_index=True,
        use_container_width=True,
    )


def main() -> None:
    st.set_page_config(page_title="Retail Store Assistant Analytics", layout="wide")
    st.title("Retail Store Assistant — Analytics Dashboard")

    if st.button("Refresh data", type="primary"):
        fetch_dashboard_data.clear()
        st.session_state["last_refreshed"] = datetime.now().strftime("%H:%M:%S")

    if "last_refreshed" not in st.session_state:
        st.session_state["last_refreshed"] = datetime.now().strftime("%H:%M:%S")
    st.caption(f"Last refreshed: {st.session_state['last_refreshed']}")

    top_products = fetch_dashboard_data("/dashboard/top-products")
    input_breakdown = fetch_dashboard_data("/dashboard/input-breakdown")
    searches_over_time = fetch_dashboard_data("/dashboard/searches-over-time")
    zero_results = fetch_dashboard_data("/dashboard/zero-results")

    left_column, right_column = st.columns(2)
    with left_column:
        show_top_products(top_products)
    with right_column:
        show_input_breakdown(input_breakdown)

    show_searches_over_time(searches_over_time)
    show_zero_result_searches(zero_results)


if __name__ == "__main__":
    main()
"@ | Out-File -FilePath dashboard\app.py -Encoding utf8