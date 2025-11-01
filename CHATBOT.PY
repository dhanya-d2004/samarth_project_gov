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
    You are an expert SQLite SQL translator. Your task is to convert natural language questions 
    into a single, correct, and executable SQLite SQL query.
    
    The database has one table named '{TABLE_NAME}'.
    The schema is as follows:
    - state_canonical (TEXT) - Primary column for state names (e.g., 'maharashtra', 'tamil nadu').
    - district (TEXT) - The district name within the state.
    - season (TEXT) - The cropping season (e.g., 'Kharif', 'Rabi').
    - month (INTEGER) - The month number (1-12).
    - rainfall_mm (REAL) - Monthly rainfall in millimeters.
    - snowfall_mm (REAL) - Monthly snowfall in millimeters.
    - area_ha (REAL) - Area under cultivation in hectares.
    - crop (TEXT) - The name of the crop (e.g., 'Rice', 'Wheat').
    - year (INTEGER) - The year of the record.
    - production_tonnes (REAL) - Total crop production in tonnes.
    - annual_rainfall_mm (REAL) - Total annual rainfall.
    - jjas_rainfall_mm (REAL) - Rainfall during June-September (Monsoon Season).
    - yield_t_per_ha (REAL) - Crop yield (tonnes per hectare).

    RULES:
    1. ALWAYS respond with a JSON object that contains a single key, 'sql_query', with the SQL query as its value. Do not include any other text or markdown outside the JSON object.
    2. Always use the table name '{TABLE_NAME}'.
    3. Use LIKE for partial or fuzzy string matching (e.g., WHERE crop LIKE '%Rice%').
    4. When querying state names, convert the input to lowercase (e.g., WHERE state_canonical = 'maharashtra').
    
    Example for 'average annual rainfall in maharashtra':
    {{"sql_query": "SELECT ROUND(AVG(annual_rainfall_mm), 2) FROM integrated_data WHERE state_canonical = 'maharashtra';"}}
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
    st.set_page_config(page_title="Samarth Agri-Climate Chatbot (LLM-Powered)", layout="centered")
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

if __name__ == '__main__':
    main()