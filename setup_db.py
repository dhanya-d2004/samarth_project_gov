import pandas as pd
import sqlite3

DATABASE_FILE = 'samarth_agri_climate.db'
CSV_FILE = 'datasets/crop_rainfall_integrated_cleaned.csv'
TABLE_NAME = 'integrated_data'

print("Starting database setup...")

# Load the CSV
df = pd.read_csv(CSV_FILE)

# Clean column names to match the names used in the LLM system prompt
df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('[^a-z0-9_]', '', regex=True)

# Connect to SQLite
conn = sqlite3.connect(DATABASE_FILE)

# Write DataFrame to the required table
df.to_sql(TABLE_NAME, conn, if_exists='replace', index=False)

conn.close()
print(f"Successfully created and populated '{DATABASE_FILE}' with table '{TABLE_NAME}'.")