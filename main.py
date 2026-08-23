import pandas as pd
import streamlit as st
from rapidfuzz import fuzz

st.title("SIH PS Search")
st.subheader("Search for SIH Problem Statements with filters")


@st.cache_data
def get_data() -> pd.DataFrame:
    df = pd.read_parquet("sih_problem_statements.parquet")
    return df


df = get_data()

# --- Sidebar filters ---
st.sidebar.header("Filters")

query = st.sidebar.text_input("Search (title + description)", "")

categories = sorted(df["category"].dropna().unique())
selected_categories = st.sidebar.multiselect("Category", categories, default=[])

themes = sorted(df["theme"].dropna().unique())
selected_themes = st.sidebar.multiselect("Theme", themes, default=[])

orgs = sorted(df["organisation"].dropna().unique())
selected_orgs = st.sidebar.multiselect("Organisation", orgs, default=[])


# --- Apply dropdown filters first (cheap, exact) ---
filtered = df.copy()

if selected_categories:
    filtered = filtered[filtered["category"].isin(selected_categories)]

if selected_themes:
    filtered = filtered[filtered["theme"].isin(selected_themes)]

if selected_orgs:
    filtered = filtered[filtered["organisation"].isin(selected_orgs)]

# --- Apply fuzzy search + ranking on top ---
if query.strip():
    # Combine title + description into one searchable haystack per row
    haystacks = (
        filtered["title"].fillna("") + " " + filtered["description"].fillna("")
    ).tolist()

    # token_set_ratio handles word reordering / partial phrase overlap well,
    # which suits "fuzzy" search on longer text better than plain ratio.
    scores = [fuzz.token_set_ratio(query, h) for h in haystacks]

    filtered = filtered.assign(match_score=scores)
    filtered = filtered[filtered["match_score"] >= 50]
    filtered = filtered.sort_values("match_score", ascending=False)
else:
    filtered = filtered.assign(match_score=None)

st.caption(f"{len(filtered)} of {len(df)} problem statements")

st.dataframe(
    filtered,
    width="stretch",
    height="content",
    hide_index=True,
    column_config={
        "match_score": st.column_config.NumberColumn("Match %", format="%d"),
    },
)

# --- CSV export of filtered results ---
csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered results as CSV",
    data=csv_bytes,
    file_name="sih_problem_statements_filtered.csv",
    mime="text/csv",
)
