# Kunal's Career AMA Chatbot

An interactive chatbot built with Streamlit and GPT-4 that answers questions about my professional background and AI expertise.

## Features
- Interactive Q&A about my background and expertise
- PDF-based context from resume and personal statement
- Chat history tracking
- Sample questions for guidance

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Place required PDF files in the root directory:
   - `resume.pdf`
   - `About Me.pdf`

3. Configure OpenAI API key in `.streamlit/secrets.toml`:
   ```toml
   OPENAI_API_KEY = "your-api-key-here"
   ```

4. Run the app:
   ```bash
   streamlit run kunal_ama_chatbot.py
   ``` 