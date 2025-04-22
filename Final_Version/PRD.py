
import streamlit as st
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import requests
from dotenv import load_dotenv
import pickle
import logging
import openrouter
import openai


# Load environment variables
load_dotenv()

# Set your OpenRouter API key 
api_key = st.secrets["OPENROUTER_API_KEY"]


client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"



# Define the PRD generation logic
def generate_prd(product_name, user_problem, key_features):
    
    prompt = f"""
You are a senior product manager. Write a one-page PRD based on the following inputs.

Product Name: {product_name}

Problem Statement: {user_problem}

Key Features: {key_features}

Structure it clearly with sections: Overview, Problem, Goals, Features.
"""
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "anthropic/claude-3-haiku",
        "messages": [
            {"role": "system", "content": "You are a senior product manager."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        return f"LLM Error: {response.status_code} – {response.text}"

# # Save PRD to Google Sheets
# def save_prd_to_sheet(product_name, user_problem, key_features, prd_text, metrics, risks):
  
#     creds_path = os.getenv("GOOGLE_SHEET_CREDENTIALS")
#     scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#     creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
#     client = gspread.authorize(creds)
#     sheet = client.open("PRD_Bot_Log").sheet1
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     sheet.append_row([timestamp, product_name, user_problem, key_features, prd_text, metrics, risks])

# Code for metrics and risks generation.
def generate_metrics_and_risks(product_name, user_problem, key_features, prd_text):
    prompt = f"""
    You are a senior product strategist. Based on the following PRD details, generate:

     4 success metrics to evaluate the product.
    ⚠️ 4 product risks that the team should watch out for.

    Product Name: {product_name}
    User Problem: {user_problem}
    Key Features: {key_features}
    PRD Summary:
    {prd_text}

    Respond in the following format:

     Success Metrics:
    - Metric 1
    - Metric 2
    - Metric 3
    - Metric 4

    ⚠️ Risks:
    - Risk 1
    - Risk 2
    - Risk 3
    - Risk 4
    """


    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "anthropic/claude-3-haiku",
        "messages": [
            {"role": "system", "content": "You are a senior product manager."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        content = result["choices"][0]["message"]["content"]

        if "⚠️" in content:
            metrics_section, risks_section = content.split("⚠️", 1)
            metrics = metrics_section.strip()
            risks = risks_section.strip()
        else:
            metrics = content.strip()
            risks = "No risks identified in the response."

        return metrics, risks
    else:
        return f"LLM Error: {response.status_code} – {response.text}", "Error retrieving risks."

# Code for designer feedback generation
def generate_designer_feedback(prd_text):
    prompt = f"""
You are a senior product designer. Based on this PRD, list 3 UX improvements and 2 design risks.

PRD:
{prd_text}
"""
    try:
        response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",  # Cheaper, solid LLM
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=500
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Error generating designer feedback: {str(e)}"


# Code for engineer feedback generation
def generate_engineer_feedback(prd_text):
    prompt = f"""
You're a senior software architect. Based on this PRD, do the following:

1. Flag any technical feasibility issues.
2. Recommend a high-level architecture (backend + frontend + infra).
3. Estimate implementation effort in dev-weeks.

PRD:
{prd_text}
"""
    try:
        response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",  # Cheaper, solid LLM
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=500
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Error generating engineer feedback: {str(e)}"


# Define LangGraph Node Functions. These functions will be called by the LangGraph framework to generate the PRD, designer feedback, engineer feedback, and metrics/risks.
def generate_prd_node(state):
    product_name = state.product_name
    user_problem = state.user_problem
    key_features = state.key_features
    
    prd = generate_prd(product_name, user_problem, key_features)
    state.prd_text = prd
    return state

def generate_designer_feedback_node(state):
    prd_text = state.prd_text
    feedback = generate_designer_feedback(prd_text)
    state.designer_feedback = feedback
    return state

def generate_engineer_feedback_node(state):
    prd_text = state.prd_text
    feedback = generate_engineer_feedback(prd_text)
    state.engineer_feedback = feedback
    return state

def generate_metrics_and_risks_node(state):
    product_name = state.product_name
    user_problem = state.user_problem
    key_features = state.key_features
    prd_text = state.prd_text
    
    metrics, risks = generate_metrics_and_risks(product_name, user_problem, key_features, prd_text)
    state.metrics = metrics
    state.risks = risks
    return state

# Define the synthesize feedback node. It cmbines the PRD, designer feedback, engineer feedback, metrics, and risks into a final PRD.
def synthesize_feedback_node(state):
    prd = state.prd_text
    designer = state.designer_feedback
    engineer = state.engineer_feedback
    metrics_output = f"Metrics:\n{state.metrics}\n\nRisks:\n{state.risks}"

    # Define the synthesize_feedback function
    def synthesize_feedback(prd, designer, engineer, metrics_output):
        return f"Final PRD:\n\n{prd}\n\nDesigner Feedback:\n{designer}\n\nEngineer Feedback:\n{engineer}\n\nMetrics and Risks:\n{metrics_output}"
    improved = synthesize_feedback(prd, designer, engineer, metrics_output)
    state.final_prd = improved
    return state


# Define the state schema using a dataclass
from dataclasses import dataclass, field
from langgraph.graph import StateGraph

@dataclass
class StateSchema:
    product_name: str = ""
    user_problem: str = ""
    key_features: str = ""
    prd_text: str = ""
    designer_feedback: str = ""
    engineer_feedback: str = ""
    metrics: str = ""
    risks: str = ""
    final_prd: str = ""


# Initialize the StateGraph with the state schema
graph = StateGraph(state_schema=StateSchema)

# Add nodes to the graph
graph.add_node("Generate PRD", generate_prd_node)
graph.add_node("Generate Designer Feedback", generate_designer_feedback_node)
graph.add_node("Generate Engineer Feedback", generate_engineer_feedback_node)
graph.add_node("Generate Metrics", generate_metrics_and_risks_node)
graph.add_node("Synthesize Final PRD", synthesize_feedback_node)


# Add edges to the graph
def route_after_prd(state):
    return "Generate Engineer Feedback" if skip_designer else "Generate Designer Feedback"

graph.set_entry_point("Generate PRD")
graph.add_conditional_edges("Generate PRD", route_after_prd)

graph.add_edge("Generate Designer Feedback", "Generate Engineer Feedback")
graph.add_edge("Generate Engineer Feedback", "Generate Metrics")
graph.add_edge("Generate Metrics", "Synthesize Final PRD")

# Compile the graph
runnable_graph = graph.compile()

#title and description

st.title("📑 PRD - Multi-Agent Edition")

# Collect user inputs
product_name = st.text_input("Product Name")
user_problem = st.text_area("User Problem")
key_features = st.text_area("Key Features")


# Define conditional logic
skip_designer = st.checkbox("Skip Designer Feedback")



# Generate PRD when button is clicked
if st.button("Generate PRD"):
    # Run the graph using the invoke method
    result_state = runnable_graph.invoke(StateSchema(
        product_name=product_name,
        user_problem=user_problem,
        key_features=key_features
    ))

    # Save state for future sessions
    with open("saved_prd_state.pkl", "wb") as f:
        pickle.dump(result_state, f)

    # Display the results
    with st.expander("📄 Product Requirements Document (PRD)"):
        st.markdown(result_state["prd_text"])

    with st.expander("🎨 Designer Agent"):
        st.markdown(result_state["designer_feedback"])

    with st.expander("🛠 Engineer Agent"):
        st.markdown(result_state["engineer_feedback"])

    with st.expander("Metrics"):
        st.text_area("Suggested Success Metrics", value=result_state["metrics"], height=200)

    with st.expander("⚠️ Risks"):
        st.text_area("Potential Risks", value=result_state["risks"], height=200)

    with st.expander("📈 Sythesizer Agent - PRD"):
        st.markdown(result_state["final_prd"])




# Handle resuming previous sessions

if os.path.exists("saved_prd_state.pkl"):
      if st.button("Resume Last Session"):
        with open("saved_prd_state.pkl", "rb") as f:
            result_state = pickle.load(f)

        with st.expander("📄 Product Requirements Document (PRD)"):
            st.markdown(result_state["prd_text"])

        with st.expander("🎨 Designer Agent"):
            st.markdown(result_state["designer_feedback"])

        with st.expander("🛠 Engineer Agent"):
            st.markdown(result_state["engineer_feedback"])

        with st.expander("Metrics"):
            st.text_area("Suggested Success Metrics", value=result_state["metrics"], height=200)

        with st.expander("⚠️ Risks"):
            st.text_area("Potential Risks", value=result_state["risks"], height=200)

        with st.expander("📈 Improved PRD"):
            st.markdown(result_state["final_prd"])




