Prerequisites:
You must have Python 3.8+ installed on your system.

Step 1: Install Dependencies
#first install the dependencies. (incase you want to create a virtual environment . create it and then install dependencies) using command
'pip install -r requirements.txt'
#type the command in the terminal of vs code


Step 2: Set Up the API Key Configuration
The application requires an OpenAI API Key for the Text-to-SQL translation.
Create a .env file in the same directory as your chatbot.py file.
Add your key to the file in the following format (replace YOUR_API_KEY_HERE):
OPENAI_API_KEY=YOUR_API_KEY_HERE
(The chatbot.py script uses python-dotenv to securely load this key.)
How to Generate Your OpenAI API Key 🔑
You need an active OpenAI account to generate an API key. This key links the usage to your account for billing.

 Create/Log in to OpenAI Account:
 
Go to the official OpenAI website and log in or create a new account.
Navigate to API Key Section:
Once logged in, go directly to the API keys section. This is usually found in your user profile settings or a dedicated "API" dashboard.
Create a New Secret Key:
Click the "Create new secret key" button.
Give your key a meaningful name (e.g., Samarth_Chatbot).
Copy the Key (CRITICAL STEP):
A unique string (starting with sk-...) will be displayed. This is the only time the key will be fully shown. Copy this key immediately.
Paste into .env:
Paste the copied key into the .env file as instructed in Step 2 of the setup guide.


Step 3: Set Up the Database
You need to load the data from the CSV file into a local SQLite database that the chatbot can query.
Ensure you have crop_rainfall_integrated_cleaned.csv in the same directory as setup_db.py.
Copy the relative path of the csv file and paste it in setup_db.py file.
Run the database setup script:
python setup_db.py
This script creates the samarth_agri_climate.db file and populates the integrated_data table.


Step 4: Run the Chatbot
Ensure your file name is lowercase (chatbot.py).
Run the Streamlit application from your terminal:
streamlit run Home.py
The application will launch in your default web browser.

