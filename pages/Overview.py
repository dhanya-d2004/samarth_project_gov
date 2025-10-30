import streamlit as st
import pandas as pd

# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(page_title="Dataset Overview", layout="wide")

# -------------------------------
# Title
# -------------------------------
st.title("📊 Dataset Overview")
st.markdown("""
This page provides an overview of the integrated dataset, including the number of unique states, districts, crops, and other key statistics.
""")

# -------------------------------
# Load Dataset
# -------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("datasets/crop_rainfall_integrated_cleaned.csv")
    return df

df = load_data()

# -------------------------------
# Display Basic Info
# -------------------------------
st.subheader("🧾 Basic Dataset Information")
st.write(f"**Total Records:** {len(df):,}")

# -------------------------------
# Summary Statistics (Distinct Counts)
# -------------------------------
col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)

with col1:
    st.metric("🌎 Total States", df["state"].nunique())

with col2:
    st.metric("🏙️ Total Districts", df["district"].nunique())

with col3:
    st.metric("📅 Total Years", df["year"].nunique())

with col4:
    st.metric("☀️ Total Seasons", df["season"].nunique() if "season" in df.columns else 0)

with col5:
    st.metric("🌾 Total Crops", df["crop"].nunique())

with col6:
    st.metric("📈 Total Columns", len(df.columns))

# -------------------------------
# Dataset Preview
# -------------------------------
st.subheader("🔍 Preview of Dataset")
st.dataframe(df.head(10))

# -------------------------------
# Optional: Column Information
# -------------------------------
with st.expander("📋 View Column Details"):
    st.write(df.dtypes)

# -------------------------------
# Insights Section
# -------------------------------
st.markdown("### 🔍 Quick Insights")
st.markdown("""
- The dataset integrates both **agricultural** and **climate (rainfall)** data across states and years.  
- Use this overview to understand data coverage before analyzing trends.  
- You can explore deeper insights in the subsequent pages like *Rainfall vs Yield*, *Yearly Trends*, and *Correlation Analysis*.
""")
