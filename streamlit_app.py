"""Streamlit backend entrypoint for deployment.

Deploy this file on Streamlit Community Cloud to run the recommendation backend
workflow without a separate API server.
"""

from __future__ import annotations

import os

import streamlit as st

from zomato_recommendation.phase1.load import load_restaurants
from zomato_recommendation.phase2.cuisine_catalog import build_cuisine_catalog
from zomato_recommendation.phase4.schemas import RecommendationRequest
from zomato_recommendation.phase4.service import run_recommendations


def _apply_streamlit_secrets_to_env() -> None:
    """Map Streamlit secrets to environment variables expected by the app."""
    if "GROQ_API_KEY" in st.secrets and not os.getenv("GROQ_API_KEY"):
        os.environ["GROQ_API_KEY"] = str(st.secrets["GROQ_API_KEY"])
    if "GROQ_MODEL" in st.secrets and not os.getenv("GROQ_MODEL"):
        os.environ["GROQ_MODEL"] = str(st.secrets["GROQ_MODEL"])


@st.cache_resource(show_spinner=False)
def _load_dataset(max_rows: int):
    return load_restaurants(max_rows=max_rows)


def main() -> None:
    st.set_page_config(page_title="Zomato AI Recommender Backend", layout="wide")
    st.title("Zomato AI Recommender Backend")
    st.caption("Streamlit deployment for backend recommendation orchestration.")

    _apply_streamlit_secrets_to_env()

    with st.sidebar:
        st.header("Runtime Settings")
        max_rows = st.number_input(
            "Rows to load from dataset",
            min_value=500,
            max_value=50000,
            value=8000,
            step=500,
            help="Larger values improve coverage but increase cold-start and memory usage.",
        )
        st.markdown(
            "Configure `GROQ_API_KEY` and optional `GROQ_MODEL` in Streamlit secrets for LLM calls."
        )

    with st.spinner("Loading and normalizing restaurant dataset..."):
        df = _load_dataset(int(max_rows))

    st.success(f"Dataset ready: {len(df)} rows loaded.")

    cuisines = build_cuisine_catalog(df)

    with st.form("recommend_form"):
        location = st.text_input("Location", placeholder="Delhi, Bangalore, etc.")
        cuisine = st.selectbox("Primary cuisine (optional)", [""] + cuisines, index=0)
        min_rating = st.slider("Minimum rating", min_value=0.0, max_value=5.0, value=4.0, step=0.1)
        use_budget = st.checkbox("Apply budget filter", value=False)
        budget_max_inr = st.number_input(
            "Budget max for two (INR)",
            min_value=100,
            max_value=50000,
            value=1500,
            step=100,
            disabled=not use_budget,
        )
        extras = st.text_input(
            "Additional preferences (optional)",
            placeholder="family-friendly, quick service",
        )
        submitted = st.form_submit_button("Run Recommendations")

    if not submitted:
        return

    if not location.strip():
        st.error("Location is required.")
        return

    request = RecommendationRequest(
        location=location.strip(),
        cuisine=cuisine,
        min_rating=min_rating,
        budget_max_inr=float(budget_max_inr) if use_budget else None,
        extras=extras.strip(),
    )

    try:
        response = run_recommendations(request, df)
    except Exception as exc:
        st.error(f"Recommendation failed: {exc}")
        return

    if response.message:
        st.info(response.message)
    if response.summary:
        st.subheader("Summary")
        st.write(response.summary)

    st.subheader("Recommendations")
    if not response.recommendations:
        st.warning("No recommendations returned for these preferences.")
    else:
        for item in response.recommendations:
            st.markdown(
                f"**#{item.rank} {item.name}**  \n"
                f"- Cuisine: {item.cuisine}  \n"
                f"- Rating: {item.rating if item.rating is not None else 'N/A'}  \n"
                f"- Estimated Cost: {item.estimated_cost}  \n"
                f"- Why this fits: {item.explanation}"
            )

    st.subheader("Meta")
    st.json(response.model_dump())


if __name__ == "__main__":
    main()
