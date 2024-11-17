from dotenv import load_dotenv
load_dotenv()  # Load all environment variables 

import streamlit as st
import os
import sqlite3
import google.generativeai as genai

# Configure API key
genai.configure(api_key=os.getenv("my_api_key"))

# Function to load Google Gemini model and provide query as response
def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([prompt[0], question])
    return response.text

# Clean up SQL query to remove unwanted characters
def clean_sql_query(sql_query):
    # Remove Markdown formatting (```sql) and extra spaces
    clean_query = sql_query.replace("```sql", "").replace("```", "").strip()
    return clean_query

# Function to retrieve query from SQL database
def read_sql_query(sql, db):

    clean_sql = clean_sql_query(sql)
    
    # Debug the cleaned query
    print(f"Executing SQL Query: {clean_sql}")

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    return rows

# Function to convert SQL results to a natural language response using the language model
def generate_natural_language_response(question, sql_query, sql_result):
    # Convert SQL results to a string format
    result_str = "\n".join([str(row) for row in sql_result])
    
    # Create a new prompt to generate natural language response
    nl_prompt = f"""
    The SQL query generated for the question "{question}" was: {sql_query}
    The result of the query is: {result_str}
    Please provide a natural language response that answers the original question based on the query results and MAKE SURE YOU INCLUDE EACH AND EVERY RESULT OF OUTPUT QUERY.
    It must not be missed.
    """
    
    # Get the natural language response from the model
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([nl_prompt])
    return response.text

# Define your prompt
prompt = [
    """

You are the best at converting college admission related questions into SQL queries! You must answer all questions by exclusively using data from the database described below. Treat this database as your knowledge base to generate SQL queries for all inquiries.

**STRICT INSTRUCTION:**
1. The SQL must not have ''' or ``` in the beginning or end and must not include the word "sql" in the output.
2. Please refer exclusively to the **Neet_PG** database for your answer. Do not search for information elsewhere. Provide your response based solely on the data in the **Neet_PG** database.

The SQL database is named **Neet_PG**, and the table name is **neet_pg_table**. It contains the following columns:

### Columns:
- **Branch**: The name of the medical branch.
- **Inst_Name**: The name of the institution.
- **college_code**: The code given to the college (e.g., **AMED**, **BMED**, **SMED**, **RMED**).
- **quota**: The type of quota (e.g., **GQ**, **IQ**, **MQ**, **UQ**, **NQ**).

### Category-Specific Fields (for each category: OPEN, SC, ST, SEBC, EWS):
- **Neet Score (SC)**: The NEET score for candidates in the SC category.
- **Neet Rank (SC)**: The NEET rank for candidates in the SC category.
- **General Merit Number of SC Candidate**: The general merit number for SC category candidates.
- **Category Merit Number (SC)**: The category-specific merit number for SC category candidates.

### Example Queries:

1. **Retrieve Information by Quota and Branch**:  
   "Show the Neet Score, Neet Rank, and General Merit Number for all candidates in the General Quota (GQ) for the Pediatrics branch."
   ```sql
   SELECT `Neet Score (SC)`, `Neet Rank (SC)`, `General Merit Number of SC Candidate` 
   FROM neet_pg_table 
   WHERE Branch = 'Pediatrics' 
   AND quota = 'GQ';
   ```

2. **Filter by Institution and Category**:  
   "List the Neet Score and Rank for SC category candidates in B. J. Medical College, Ahmedabad."
   ```sql
   SELECT `Neet Score (SC)`, `Neet Rank (SC)` 
   FROM neet_pg_table 
   WHERE Inst_Name = 'B. J. Medical College, Ahmedabad' 
   AND quota = 'GQ';
   ```

3. **Aggregate Data**:  
   "Count the total number of candidates who scored above 500 in the SC category across all branches."
   ```sql
   SELECT COUNT(*) 
   FROM neet_pg_table 
   WHERE `Neet Score (SC)` > 500;
   ```

4. **Specific Merit Numbers Across Categories**:  
   "Find the Category Merit Number for SEBC candidates for the Orthopaedics branch at any institution with an MQ (Management Quota) label."
   ```sql
   SELECT `Category Merit Number (SC)` 
   FROM neet_pg_table 
   WHERE Branch = 'Orthopaedics' 
   AND quota = 'MQ';
   ```

    """
]

# Streamlit App
st.set_page_config(page_title="LLM with SQL2NL")
st.header("I will happily answer your NEET Admission Related Queries !!")

question = st.text_input("Input:", key='input')
submit = st.button("Ask the Question")

# If submit is clicked
if submit:
    sql_query = get_gemini_response(question, prompt)
    print(sql_query)
    sql_result = read_sql_query(sql_query, "Neet_PG.db")
    natural_language_response = generate_natural_language_response(question, sql_query, sql_result)
    st.subheader("The Response is: ")
    st.write(natural_language_response)