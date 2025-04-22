import datetime
import os
import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
load_dotenv()

st.title("🧠 Multi-Agent PRD Bot")

prd_text = st.text_area("Paste your PRD here", height=300)

if st.button("Run Multi-Agent Analysis"):
    with st.spinner("Agents are analyzing..."):
        results = run_multi_agent_loop(prd_text)

    with st.expander("📏 Metrics & Risks Agent"):
        st.markdown(results["Metrics Agent"])

    st.subheader("🎨 Designer Agent")
    st.markdown(results["Designer Agent"])

    st.subheader("🧑‍💻 Engineer Agent")
    st.markdown(results["Engineer Agent"])

    st.subheader("🧠 PM Synthesizer Agent")
    st.markdown(results["PM Synthesizer Agent"])

# Save PRD to Google Sheets
def save_prd_to_sheet(product_name, user_problem, key_features, prd_text, metrics, risks):
    creds_path = os.getenv("GOOGLE_SHEET_CREDENTIALS")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    sheet = client.open("PRD_Bot_Log").sheet1
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, product_name, user_problem, key_features, prd_text, metrics, risks])

      # Save the PRD to Google Sheets
    save_prd_to_sheet(product_name, user_problem, key_features, prd_text, metrics, risks)