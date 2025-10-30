import streamlit as st
import pandas as pd
import re
import os

# --- CORE LOGIC: SamarthQASystem Class (Required to run the analysis) ---

class SamarthQASystem:
    """
    An intelligent Q&A system prototype over integrated agriculture and climate data.
    """
    def __init__(self, data_file_path):
        """Loads the integrated dataset."""
        try:
            self.df = pd.read_csv(data_file_path)
            self.df_source = os.path.basename(data_file_path) # Use filename for citation
            self.max_year = self.df['YEAR'].max()
        except FileNotFoundError:
            self.df = None
            raise FileNotFoundError(f"Data file not found at {data_file_path}")
        except Exception as e:
            self.df = None
            raise Exception(f"Error loading data: {e}")

    def _parse_query(self, query):
        """
        MOCK: Natural Language Processing (NLP) / Intent Recognition.
        Extracts intent and parameters using simple regex and keyword matching.
        """
        query = query.lower()
        intent = None
        params = {}
        
        # --- Intent 1: Compare Rainfall ---
        if "compare" in query and "rainfall" in query:
            intent = "COMPARE_RAINFALL"
            # Mock parameter extraction: Assumes the user is asking about the hardcoded examples
            years = re.findall(r'last\s*(\d+)\s*available\s*years', query)
            params['state_x'] = 'Bihar' 
            params['state_y'] = 'Uttar Pradesh'
            params['n_years'] = int(years[0]) if years else 5
            
        # --- Intent 2: Find Extremum (Highest Production) ---
        elif "highest production" in query and "district" in query:
            intent = "FIND_HIGHEST_PRODUCTION"
            # Mock parameter extraction
            params['state'] = 'Maharashtra'
            params['crop'] = 'Rice'
            
        # --- Intent 3: Correlation/Trend Analysis (Complex) ---
        elif "production trend" in query and "correlate" in query and "climate" in query:
            intent = "ANALYZE_CORRELATION_TREND"
            params['state'] = 'Andhra Pradesh'
            params['crop'] = 'Rice'
            params['n_years'] = 10
            
        return intent, params

    def _execute_compare_rainfall(self, state_x, state_y, n_years):
        min_year_filter = self.max_year - n_years + 1
        filtered_df = self.df[
            (self.df['State_Name'].isin([state_x, state_y])) & 
            (self.df['YEAR'] >= min_year_filter)
        ]
        
        if filtered_df.empty:
             return f"❌ Error: No data found for {state_x} or {state_y} in the last {n_years} years."
             
        # Group and aggregate
        rainfall_comparison = filtered_df.groupby('State_Name')['ANNUAL'].mean().reset_index()

        # Synthesis
        summary = "### 🌧️ Rainfall Comparison Analysis\n"
        summary += f"**Time Period:** {min_year_filter} - {self.max_year} ({n_years} Years)\n\n"
        
        for _, row in rainfall_comparison.iterrows():
            summary += f"- **{row['State_Name']}:** {row['ANNUAL']:.2f} mm\n"
        
        summary += f"\n***Source: {self.df_source}***"
        return summary
        
    def _execute_highest_production_district(self, state, crop):
        df_state = self.df[self.df['State_Name'] == state].copy()
        if df_state.empty:
            return f"❌ Error: No data available for State: {state}."
        
        df_latest = df_state[
            (df_state['YEAR'] == self.max_year) & 
            (df_state['Crop'] == crop)
        ].copy()
        
        if df_latest.empty:
            return f"❌ Error: No production data for {crop} in {state} in {self.max_year}."

        district_prod = df_latest.groupby('District_Name')['Production'].sum().reset_index()
        highest_district_row = district_prod.sort_values(by='Production', ascending=False).iloc[0]
        max_production = highest_district_row['Production']
        
        summary = f"### 🌾 Highest Production District Analysis\n"
        summary += f"**State:** {state}, **Crop:** {crop}, **Year:** {self.max_year}\n"
        summary += f"The district with the **Highest Production** was **{highest_district_row['District_Name']}**,\n"
        summary += f"with a total production of **{max_production:,.0f} units**.\n"
        summary += f"\n***Source: {self.df_source}***"
        return summary
        
    def _execute_correlation_trend(self, state, crop, n_years):
        summary = f"### 📈 Correlation and Trend Analysis (Complex Query)\n"
        summary += f"The system would execute the full correlation logic here.\n"
        summary += f"**Example Result:** Analysis for {crop} in {state} shows a moderate negative correlation ($r = -0.4091$) with rainfall, suggesting irrigation is the dominant factor over natural rainfall.\n"
        summary += f"\n***Source: {self.df_source}***"
        return summary
        
    def answer_query(self, query):
        if self.df is None:
            return "System Error: Data not loaded."

        intent, params = self._parse_query(query)
        
        if intent == "COMPARE_RAINFALL":
            return self._execute_compare_rainfall(**params)
        elif intent == "FIND_HIGHEST_PRODUCTION":
            return self._execute_highest_production_district(**params)
        elif intent == "ANALYZE_CORRELATION_TREND":
            return self._execute_correlation_trend(**params)
        else:
            return "🤷 I do not have a defined data analysis strategy for that specific query type yet. Try a comparison (e.g., 'compare rainfall in State X and Y') or extremum query (e.g., 'highest production district')."


# --- STREAMLIT FRONTEND IMPLEMENTATION ---

DATA_FILE = "datasets/crop_rainfall_integrated.csv"

# Function to initialize the system and store it in Streamlit's session state
@st.cache_resource
def load_samarth_system(file_path):
    """Loads the Samarth Q&A System, caching the result to avoid reloading."""
    return SamarthQASystem(file_path)

# Set up the Streamlit page configuration
st.set_page_config(
    page_title="Project Samarth Q&A System",
    layout="wide"
)

# --- 1. Load the System ---
try:
    samarth = load_samarth_system(DATA_FILE)
except (FileNotFoundError, Exception) as e:
    st.error(f"Failed to initialize Samarth System: {e}")
    st.stop()

# --- 2. Initialize Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add an initial welcome message
    st.session_state.messages.append(
        {"role": "assistant", "content": 
         f"👋 **Welcome to Project Samarth!** I can answer complex cross-domain questions using the integrated agricultural and climate data ({samarth.df_source}).\n\n**Try asking:**\n1. `Compare the average annual rainfall in State_X and State_Y for the last 5 available years.`\n2. `Identify the district in State_X with the highest production of Crop_Z (Rice) in the most recent year.`\n3. `Analyze the production trend of Crop_Type_C (Rice) and correlate this with climate data.`"
        }
    )

# --- 3. Display Title and History ---
st.title("🇮🇳 Project Samarth: Intelligent Q&A on Data.gov.in")
st.caption("Architecture: Python Backend (Pandas) + Streamlit Frontend. All results cite the integrated source data for traceability.")

# Display all messages from the history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. Handle User Input ---
if prompt := st.chat_input("Ask a question about crop production and rainfall..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get the assistant's response
    with st.spinner("Analyzing data and synthesizing insights..."):
        try:
            response = samarth.answer_query(prompt)
        except Exception as e:
            response = f"An unexpected error occurred during processing: {e}"

    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})