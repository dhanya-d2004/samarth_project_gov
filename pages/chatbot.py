import streamlit as st
import sqlite3
import pandas as pd
import os
from typing import Optional, Dict
from pydantic import BaseModel, Field
from dotenv import load_dotenv
# NEW IMPORTS
from openai import OpenAI
import json
load_dotenv() # <--- MUST BE THE FIRST CALL to load variables
DATABASE_FILE = 'samarth_agri_climate.db'
TABLE_NAME = 'integrated_data'


# --- 1. OpenAI Configuration ---

# 1. Explicitly fetch the key after load_dotenv() runs
API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client.
try:
    # 2. Check if the key was successfully loaded
    if not API_KEY:
        # Raise a clear error if the key is missing from the .env file
        raise ValueError("OPENAI_API_KEY not found in environment. Check your .env file.")

    # 3. Explicitly pass the key to the OpenAI client
    client = OpenAI(api_key=API_KEY)
    
except Exception as e:
    # This error handling now catches both the ValueError and API client errors
    st.error(f"Failed to initialize OpenAI client. Check your API key. Error: {e}")
    client = None

# Pydantic schema for reliable JSON output from the LLM
class SQLQuery(BaseModel):
    """A Pydantic model to ensure the LLM output is a valid SQL query."""
    sql_query: str = Field(description="The executable SQLite SQL query.")


def prompt_to_sql(prompt: str) -> Optional[str]:
    """
    Translates a natural language prompt into an SQL query using the OpenAI API.
    """
    if client is None:
        return None
    
    # --- UPDATED SYSTEM PROMPT ---
    SYSTEM_PROMPT = f"""
    You are an expert SQLite SQL translator, specializing in agricultural and climate data analysis. Your task is to convert complex natural language questions into a single, correct, and executable SQLite SQL query.
    
    The database has one table named '{TABLE_NAME}'.
    The schema is as follows:
    - state_canonical (TEXT) - Primary column for state names (must be lowercase).
    - district (TEXT) - The district name.
    - area_ha (REAL) - Area under cultivation in hectares.
    - season (TEXT) - The agricultural season (e.g., Kharif, Rabi).
    - crop (TEXT) - The name of the crop (must use LIKE for flexible matching).
    - year (INTEGER) - The year of the record.
    - production_tonnes (REAL) - Total crop production in tonnes.
    - annual_rainfall_mm (REAL) - Total annual rainfall.
    - jjas_rainfall_mm (REAL) - Rainfall during June-September (Monsoon Season).
    - yield_t_per_ha (REAL) - Crop yield (tonnes per hectare).

    RULES (STRICTLY FOLLOWED):
    1. SINGLE STATEMENT ONLY: ALWAYS generate exactly ONE executable SQL statement. DO NOT use semicolons (;) to separate multiple statements.
    2. PARALLEL DATA (UNION ALL): If the user asks for two UNRELATED metrics (e.g., Rainfall AND Production), use UNION ALL to combine the results into a single table. The column headers must be consistent across both SELECT statements.
    3. TIME FILTERING: For time periods (e.g., 'last 10 years'), use the format: `year >= (SELECT MAX(year) - N FROM {TABLE_NAME})`. DO NOT use date functions like strftime() on the 'year' column.
    4. RANKING/COMPARISON: For 'highest,' 'lowest,' or 'compare' questions, use GROUP BY, SUM/AVG, ORDER BY, and LIMIT.
    5. STRING MATCHING: Use `LOWER(state_canonical) = '...'` for states and `crop LIKE '%...%'` for crops to handle casing and slight variations.
    6. ALWAYS generate exactly ONE executable SQL statement. Your entire response MUST be a **valid JSON object** containing a single key, 'sql_query'.
    7. REGION MATCHING: For multi-word regions (e.g., 'andaman and nicobar islands'), use the full, exact name. Alternatively, use the LIKE operator for robustness: `WHERE state_canonical LIKE '%andaman and nicobar%'`.
    # --- ADVANCED TEMPLATE EXAMPLES ---

    # 1. TEMPLATE: Parallel Comparison (Rainfall & Production)
    # The query must return two separate data blocks using UNION ALL.
    # The final columns must be generic (e.g., 'Metric', 'Value', 'Context').
    
    Example for 'Compare average annual rainfall in Karnataka and Kerala for the last 5 years. In parallel, list the highest rice production in each of those states during the same period.':
    {{"sql_query": "SELECT state_canonical AS Region, 'Avg_Rainfall_mm' AS Metric, ROUND(AVG(annual_rainfall_mm), 2) AS Value, 'N/A' AS Context FROM integrated_data WHERE (state_canonical = 'karnataka' OR state_canonical = 'kerala') AND year >= (SELECT MAX(year) - 5 FROM integrated_data) GROUP BY state_canonical UNION ALL SELECT state_canonical AS Region, 'Max_Rice_Production' AS Metric, SUM(CASE WHEN crop LIKE '%Rice%' THEN production_tonnes ELSE 0 END) AS Value, 'Total Rice Production' AS Context FROM integrated_data WHERE (state_canonical = 'karnataka' OR state_canonical = 'kerala') AND year >= (SELECT MAX(year) - 5 FROM integrated_data) GROUP BY state_canonical;"}}

    # 2. TEMPLATE: District Comparison (Ranking with Subqueries)
    # This requires nested queries to find MAX/MIN in different states using a subquery for each part.
    
    Example for 'Identify the district in State_X with the highest production of Crop_Z in the most recent year available and compare that with the district with the lowest production of Crop_Z in State_Y.':
    {{"sql_query": "SELECT 'Highest in West Bengal' AS Comparison, district, production_tonnes FROM (SELECT district, production_tonnes FROM integrated_data WHERE state_canonical = 'west bengal' AND crop LIKE '%Wheat%' AND year = (SELECT MAX(year) FROM integrated_data) ORDER BY production_tonnes DESC LIMIT 1) UNION ALL SELECT 'Lowest in Bihar' AS Comparison, district, production_tonnes FROM (SELECT district, production_tonnes FROM integrated_data WHERE state_canonical = 'bihar' AND crop LIKE '%Wheat%' AND year = (SELECT MAX(year) - 1 FROM integrated_data) ORDER BY production_tonnes ASC LIMIT 1);"}}
    # 3. TEMPLATE: Correlation/Trend Analysis (Time Series)
    # Focuses on selecting time-series data for synthesis.

    Example for 'Analyze the production trend of Wheat in Punjab over the last decade and correlate with climate data.':
    {{"sql_query": "SELECT year, SUM(production_tonnes) AS Production, AVG(annual_rainfall_mm) AS Annual_Rainfall, AVG(yield_t_per_ha) AS Average_Yield FROM integrated_data WHERE state_canonical = 'punjab' AND crop LIKE '%Wheat%' AND year >= (SELECT MAX(year) - 10 FROM integrated_data) GROUP BY year ORDER BY year;"}}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            # FIX: Use response_format for JSON mode
            response_format={"type": "json_object"}, 
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0 # Use low temperature for deterministic SQL generation
        )
        
        # FIX: Manually parse the JSON string from the response
        json_content = response.choices[0].message.content
        parsed_json = json.loads(json_content)
        
        # Extract the query from the parsed JSON object
        return parsed_json.get("sql_query")
        
    except Exception as e:
        # If the JSON parsing fails or the API call errors
        st.error(f"OpenAI API Error: {e}")
        return None


# --- 2. Database Execution Engine ---

def execute_sql(sql_query: str) -> Optional[pd.DataFrame | str]:
    """
    Executes the generated SQL query against the SQLite database.
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        result_df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return result_df
    except sqlite3.Error as e:
        return str(e)
    except Exception as e:
        return f"Unexpected execution error: {str(e)}"

# --- 3. Answer Synthesis (Simplified for this example) ---

def synthesize_answer(df: pd.DataFrame, prompt: str) -> str:
    """
    Uses the LLM to summarize the data query result.
    """
    if client is None:
        return "Synthesis skipped: OpenAI client not initialized."
        
    # Create a concise string representation of the data frame
    data_summary = df.head(5).to_markdown(index=False)
    
    synthesis_prompt = f"""
    You are an agricultural data analyst. Summarize the key findings from the provided 
    data result in a concise, human-readable sentence. 
    
    Original Question: "{prompt}"
    
    Data Result (Top 5 Rows):
    {data_summary}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": synthesis_prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Failed to synthesize answer: {e}"


# --- 4. Streamlit UI (Main Application Flow) ---

def main():
    # Removed st.set_page_config() to allow Home.py to manage config
    st.title("🌾 Samarth Agri-Climate Chatbot")
    st.markdown("Ask natural language questions about crop production, rainfall, and trends.")
    
    if client is None:
        st.warning("Please set the OPENAI_API_KEY environment variable to start.")
        return

    # Check for the database file
    if not os.path.exists(DATABASE_FILE):
        st.error(f"Database file not found: {DATABASE_FILE}. Please run the ETL to create it.")
        return

    user_prompt = st.text_input(
        "Your Query:",
        placeholder="e.g., What was the average rice production in Bihar?",
        key="prompt"
    )

    if st.button("Ask Samarth", key="ask_button") and user_prompt:
        
        # --- LLM Parsing Step ---
        st.info("Parsing query using LLM...")
        sql_query = prompt_to_sql(user_prompt)

        if sql_query:
            st.success("Query Parsed! Executing SQL...")
            st.code(sql_query, language="sql")
            
            # --- Database Execution Step ---
            result = execute_sql(sql_query)
            
            if isinstance(result, pd.DataFrame):
                if not result.empty:
                    
                    # --- LLM Synthesis Step ---
                    s_answer = synthesize_answer(result, user_prompt)
                    st.header("Answer")
                    st.success(s_answer)
                    
                    # --- Data Display ---
                    st.subheader("Raw Data Query Output")
                    st.dataframe(result, use_container_width=True)
                    
                else:
                    st.warning("No data found for the specified criteria. Check your spelling or criteria.")
            else:
                # If result is a string, it's an error message
                st.error(f"An error occurred during execution: {result}")
        else:
            st.warning("Sorry, the LLM could not generate a valid SQL query or the API call failed.")

# Call the main function to run the app
main()