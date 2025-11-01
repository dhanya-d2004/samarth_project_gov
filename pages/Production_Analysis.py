import streamlit as st
import pandas as pd
import plotly.express as px

st.title("🌾 Crop Production Analysis")

df = pd.read_csv("datasets/crop_rainfall_integrated_cleaned.csv")

crop = st.selectbox("Select Crop", df['crop'].unique())
subset = df[df['crop'] == crop]

fig = px.bar(subset.groupby('state')['production_tonnes'].sum().reset_index(),
             x='state', y='production_tonnes',
             title=f"Total Production by State for {crop}")
st.plotly_chart(fig, use_container_width=True)
