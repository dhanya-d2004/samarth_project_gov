import streamlit as st
import pandas as pd
import plotly.express as px

st.title("🌦️ Rainfall Trend Analysis")

df = pd.read_csv("datasets/crop_rainfall_integrated_cleaned.csv")

state = st.selectbox("Select State", df['state'].unique())
subset = df[df['state'] == state]

fig = px.line(subset, x='year', y='annual_rainfall_mm', title=f"Annual Rainfall Trend - {state}")
st.plotly_chart(fig, use_container_width=True)
