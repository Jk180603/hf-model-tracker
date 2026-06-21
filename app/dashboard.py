"""
Streamlit Dashboard — HuggingFace Model Trends
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

st.set_page_config(
    page_title="HuggingFace Model Trends",
    page_icon="🤗",
    layout="wide"
)

st.title("🤗 HuggingFace AI Model Trends 2026")
st.markdown("Real-time analysis of 500+ AI models scraped from the HuggingFace Hub")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("data/hf_models_clean.csv")
    return df

try:
    df = load_data()
except:
    st.error("Run the pipeline first: python src/scraper.py && python src/etl.py")
    st.stop()

# Metrics row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Models", f"{len(df):,}")
col2.metric("Active (90 days)", f"{df['is_actively_maintained'].sum():,}")
col3.metric("Total Downloads", f"{df['downloads_last_month'].sum():,.0f}")
col4.metric("Unique Tasks", f"{df['task'].nunique()}")

st.divider()

# Two column layout
left, right = st.columns(2)

with left:
    st.subheader("📊 Top Tasks by Downloads")
    task_data = df.groupby("task")["downloads_last_month"].sum().sort_values(ascending=False).head(10)
    fig1 = px.bar(
        x=task_data.values,
        y=task_data.index,
        orientation="h",
        color=task_data.values,
        color_continuous_scale="Viridis"
    )
    fig1.update_layout(
        height=400,
        showlegend=False,
        xaxis_title="Total Downloads (Last Month)",
        yaxis_title="",
        coloraxis_showscale=False
    )
    st.plotly_chart(fig1, use_container_width=True)

with right:
    st.subheader("🧠 Architecture Distribution")
    arch_data = df["architecture"].value_counts().head(8)
    fig2 = px.pie(
        values=arch_data.values,
        names=arch_data.index,
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

left2, right2 = st.columns(2)

with left2:
    st.subheader("🎯 Use Case Breakdown")
    uc_data = df.groupby("use_case").agg(
        count=("model_id", "count"),
        downloads=("downloads_last_month", "sum")
    ).sort_values("downloads", ascending=False)
    fig3 = px.treemap(
        names=uc_data.index,
        parents=["" for _ in uc_data.index],
        values=uc_data["downloads"],
        color=uc_data["count"],
        color_continuous_scale="Blues"
    )
    fig3.update_layout(height=400, coloraxis_showscale=False)
    st.plotly_chart(fig3, use_container_width=True)

with right2:
    st.subheader("📚 Library Ecosystem")
    lib_data = df["library"].value_counts().head(8)
    fig4 = px.bar(
        x=lib_data.index,
        y=lib_data.values,
        color=lib_data.values,
        color_continuous_scale="Magma"
    )
    fig4.update_layout(
        height=400,
        showlegend=False,
        xaxis_title="",
        yaxis_title="Model Count",
        coloraxis_showscale=False
    )
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# Download tier distribution
st.subheader("📈 Download Tier Distribution")
tier_data = df["download_tier"].value_counts()
fig5 = px.bar(
    x=tier_data.index.astype(str),
    y=tier_data.values,
    color=tier_data.index.astype(str),
    color_discrete_map={
        "tiny": "#636EFA",
        "small": "#EF553B",
        "medium": "#00CC96",
        "popular": "#AB63FA",
        "viral": "#FFA15A"
    }
)
fig5.update_layout(height=350, showlegend=False, xaxis_title="Tier", yaxis_title="Count")
st.plotly_chart(fig5, use_container_width=True)

st.divider()

# Top 10 models table
st.subheader("🏆 Top 10 Most Downloaded Models")
top10 = df.nlargest(10, "downloads_last_month")[
    ["model_id", "task", "architecture", "downloads_last_month", "likes", "popularity_score"]
].reset_index(drop=True)
top10.index = top10.index + 1
st.dataframe(top10, use_container_width=True)

# Search
st.divider()
st.subheader("🔍 Search Models")
query = st.text_input("Search by model name, task, or architecture")
if query:
    results = df[
        df["model_id"].str.contains(query, case=False, na=False) |
        df["task"].str.contains(query, case=False, na=False) |
        df["architecture"].str.contains(query, case=False, na=False)
    ][["model_id", "task", "architecture", "downloads_last_month", "likes"]].head(20)
    st.dataframe(results, use_container_width=True)

st.divider()
st.caption("Data scraped from HuggingFace Hub API · Built by Jay Khakhar · github.com/Jk180603")