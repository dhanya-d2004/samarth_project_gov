import streamlit as st
import pandas as pd
import plotly.express as px

st.title("🗺️ Statewise Insights")

df = pd.read_csv("datasets/crop_rainfall_integrated_cleaned.csv")

state = st.selectbox("Select State", df['state'].unique())
state_df = df[df['state'] == state]

fig = px.bar(state_df.groupby('crop')['yield_t_per_ha'].mean().reset_index(),
             x='crop', y='yield_t_per_ha',
             title=f"Average Yield by Crop in {state}")
st.plotly_chart(fig, use_container_width=True)
