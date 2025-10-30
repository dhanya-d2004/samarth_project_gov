import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(page_title="Rainfall vs Yield by Place", layout="wide")

# -------------------------------
# Title and Description
# -------------------------------
st.title("🌾 Rainfall vs Yield by Place")
st.markdown("""
Explore how **rainfall** and **crop yield** have changed over the years  
for any selected **crop** and **location (state/district)**.
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
# Check necessary columns
# -------------------------------
required_columns = ["crop", "state", "district", "year", "annual_rainfall_mm", "yield_t_per_ha"]
missing_cols = [col for col in required_columns if col not in df.columns]
if missing_cols:
    st.error(f"❌ Missing columns in dataset: {', '.join(missing_cols)}")
    st.stop()

# -------------------------------
# User Inputs: Crop & Place
# -------------------------------
col1, col2 = st.columns(2)

with col1:
    crop_options = sorted(df["crop"].dropna().unique())
    selected_crop = st.selectbox("🌱 Select Crop:", crop_options)

with col2:
    place_type = st.radio("Select Place Type:", ["State", "District"], horizontal=True)

if place_type == "State":
    place_options = sorted(df["state"].dropna().unique())
else:
    place_options = sorted(df["district"].dropna().unique())

selected_place = st.selectbox(f"📍 Select {place_type}:", place_options)

# -------------------------------
# Filter Data
# -------------------------------
if place_type == "State":
    filtered_df = df[(df["crop"] == selected_crop) & (df["state"] == selected_place)]
else:
    filtered_df = df[(df["crop"] == selected_crop) & (df["district"] == selected_place)]

if filtered_df.empty:
    st.warning("⚠️ No data found for the selected crop and place.")
    st.stop()

# -------------------------------
# Prepare Data for Chart
# -------------------------------
chart_df = (
    filtered_df.groupby("year")[["annual_rainfall_mm", "yield_t_per_ha"]]
    .mean()
    .reset_index()
    .sort_values("year")
)

# -------------------------------
# Plot: Rainfall vs Yield Over Time
# -------------------------------
st.subheader(f"📊 Yearly Rainfall vs Yield Trend for {selected_crop} in {selected_place}")

fig = px.line(
    chart_df,
    x="year",
    y=["annual_rainfall_mm", "yield_t_per_ha"],
    markers=True,
    title=f"Rainfall and Yield Trend ({selected_crop} - {selected_place})",
    labels={
        "value": "Value",
        "variable": "Parameter",
        "year": "Year",
    },
)

fig.update_traces(line=dict(width=3))
fig.update_layout(
    legend_title_text="Parameter",
    xaxis_title="Year",
    yaxis_title="Value",
    template="plotly_dark",
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# Insights
# -------------------------------
st.markdown("### 🔍 Insights")
st.markdown(f"""
- The graph shows how **rainfall** and **yield** for **{selected_crop}** have varied across years in **{selected_place}**.  
- Increasing rainfall with flat or dropping yield might indicate inefficiencies or crop stress.  
- Consistent upward trends in both indicate favorable climate and good agricultural performance.  
""")
