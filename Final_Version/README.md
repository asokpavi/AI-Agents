#  PRD- Multi-Agent Edition

This Streamlit app generates full-fledged Product Requirement Documents (PRDs) using AI agents—Product Manager, Designer, Engineer, and Synthesizer. Built with OpenRouter LLMs and LangGraph, it gives you a real-world view of how autonomous agents can collaborate.

## ⚙️ Features

- ✅ One-page PRD generation via Claude-3 Haiku
- 🖌️ UX feedback from a virtual Senior Designer
- 🛠️ Feasibility and architecture advice from a virtual Engineer
- 📏 Suggested success metrics and risks
- 📈 Synthesized final PRD for product review
- 💾 Google Sheets logging (optional)
- 🔁 Session resumption using Pickle
- 🚀 Built using LangGraph for flexible orchestration

## 🧠 Architecture

- **LangGraph** controls the flow between agents
- **OpenRouter LLMs** for Claude 3 Haiku + Mistral 7B
- **Streamlit** for UI
- **gspread + Google Sheets** to log outputs (optional)
- **dotenv** for local env management

## 📦 Installation

```bash
git clone https://github.com/yourusername/prd-multi-agent.git
cd prd-multi-agent
pip install -r requirements.txt

## Run the file
streamlit run PRD.py
