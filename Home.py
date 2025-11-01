import streamlit as st
import pandas as pd

st.set_page_config(page_title="Project Samarth - EDA Dashboard", layout="wide")

st.title("🌾 Project Samarth: Agricultural & Rainfall Data Explorer")

st.markdown("""
Welcome to the **EDA Dashboard** for India's agriculture and climate dataset.
Use the sidebar or tabs above to explore:
- 📈 Data Overview
- 🌦️ Rainfall Analysis
- 🌾 Crop Production Trends
- 📊 Yield vs Rainfall Correlation
- 🗺️ Statewise Insights
- 🤖 **LLM Chatbot** (New!)(prototype)
""")

# Load dataset
@st.cache_data
def load_data():
    df = pd.read_csv("datasets/crop_rainfall_integrated_cleaned.csv")
    return df

df = load_data()

st.subheader("Data Preview")
st.dataframe(df.head())

st.markdown("**Dataset Dimensions:**")
st.write(f"Rows: {df.shape[0]} | Columns: {df.shape[1]}")