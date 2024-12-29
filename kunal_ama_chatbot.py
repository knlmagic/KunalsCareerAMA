import streamlit as st
import difflib
from openai import OpenAI
import PyPDF2
import os
from datetime import datetime

# Configure OpenAI API
if 'OPENAI_API_KEY' not in st.secrets:
    st.error("Please set your OpenAI API key in Streamlit secrets!")
    st.stop()

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])

def read_pdf_file(file_path, file_type):
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        st.error(f"Error reading {file_type}: {str(e)}")
        return None

def save_chat_history(question, answer):
    """Save chat history to a file with timestamp"""
    # Create chat_history directory if it doesn't exist
    os.makedirs("chat_history", exist_ok=True)
    
    # Generate timestamp and filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_history/chat_{timestamp}.txt"
    
    # Save chat to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Question: {question}\n")
        f.write(f"Answer: {answer}\n")
        f.write("-" * 50 + "\n")

def append_to_master_log(question, answer):
    """Append chat to a master log file"""
    master_log = "chat_history/master_chat_log.txt"
    with open(master_log, "a", encoding="utf-8") as f:
        f.write(f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Question: {question}\n")
        f.write(f"Answer: {answer}\n")
        f.write("-" * 50 + "\n")

# Read both PDF files
resume_content = read_pdf_file("resume.pdf", "resume")
about_me_content = read_pdf_file("About Me.pdf", "About Me document")

if resume_content is None or about_me_content is None:
    st.error("Required PDF files not found. Please ensure both resume.pdf and About Me.pdf are in the same directory.")
    st.stop()

# Title
st.title("Ask Kunal - AI Solutions AMA")

# Intro
st.write("""
Welcome! This is Kunal's interactive GenAI agent to help you learn about Kunal's background, expertise, and vision for AI at VSP Vision's Global Innovation Center. 

         Type a question below to get started.
""")

# Predefined Questions and Answers
qa_pairs = {
    "What is your background?": "I have 24+ years of experience in technology consulting and client partnerships, specializing in the US Financials Services industry. My expertise includes AI strategy, digital transformation, and building scalable solutions.",
    "What is your vision for AI in vision care?": "AI has the potential to revolutionize vision care by enabling predictive diagnostics, personalized treatment plans, and AI-powered visual aids. I believe the focus should be on combining ethical AI practices with impactful business outcomes.",
    "How do you lead AI adoption?": "I emphasize an incremental approach—identifying quick wins while laying the foundation for long-term scalability. AI governance, employee enablement, and measurable ROI are at the core of my approach.",
    "Can you scale AI teams?": "Yes, I have experience scaling AI teams by focusing on skill diversity, process automation, and empowering cross-functional collaboration to achieve faster AI deployments.",
    "What challenges do you foresee for AI?": "Key challenges include ensuring data privacy, overcoming adoption resistance, and aligning AI outcomes with business goals. Tackling these requires a blend of strategy, governance, and stakeholder alignment."
}

def get_gpt4_response(question):
    try:
        system_prompt = f"""You are Kunal, a GenAI expert currently helping enterprises define and drive their enterprise AI strategies, and would like to lead AI initiatives at VSP Vision's Global Innovation Center. 
        You are kind, compassionate, and empathetic. You are also a great listener and a great communicator. You enjoy helping people and making a difference.
        You believe in the power of AI to transform businesses and improve lives. Starting with learning about VSP Vision's Global Innovation Center and its mission to transform vision care, you are eager to learn more about the company and its culture.
        Your responses should be based STRICTLY on the following information and nothing else:

        Bold market point of view:
Generative AI is flipping the script on software development: we're moving from rigid GUIs to adaptive, Generative and Conversational UIs that focus on delivering real business value, powered by 'thinking' software vs legacy programmatic logic.
The old Agile/SAFe playbooks can't keep pace with LLM-enabled apps that learn and pivot in real time. 
We have to rethink everything— application technology stack, operating models, development cycles, and how we measure success—as conversation replaces clicks. 
But the biggest obstacle right now is closing the knowledge gap. Many teams aren't sure how to build and deploy LLM-based applications, and while IT folks might "get it" at a conceptual level, the business side often lags. 
There's confusion on where to start, how to measure success, and how to transform old operating models into AI-native frameworks.

        Resume Information:
        {resume_content}

        Additional Background Information:
        {about_me_content}

        Important rules:
        1. ONLY provide information that is explicitly mentioned in the documents above
        2. If asked about something not covered in the documents, say "I don't have that information in my background documents"
        3. Keep responses concise and professional
        4. Do not make assumptions or add information not present in the documents
        5. If asked about future vision or opinions, base them on the experience and expertise shown in the documents
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error connecting to OpenAI: {str(e)}")
        return "I apologize, but I'm having trouble connecting to the AI service. Please try again later."

def find_best_match(user_question, questions):
    # Convert user question to lowercase for comparison
    user_question = user_question.lower()
    
    # Find the closest matching question
    matches = difflib.get_close_matches(
        user_question,
        [q.lower() for q in questions],
        n=1,
        cutoff=0.6
    )
    
    # If we found a match, return the original (non-lowercase) question
    if matches:
        # Find the original question with case preserved
        for original_q in questions:
            if original_q.lower() == matches[0]:
                return original_q
    return None

# Initialize chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Chatbot Input and Response
with st.form(key='my_form', clear_on_submit=True):
    user_question = st.text_input("Ask a question:")
    submit_button = st.form_submit_button("Ask")

if submit_button and user_question:
    # Get response using GPT-4 with the resume context
    response = get_gpt4_response(user_question)
    
    # Save chat history to files
    save_chat_history(user_question, response)
    append_to_master_log(user_question, response)
    
    # Add to session state chat history
    st.session_state.chat_history.append({"question": user_question, "answer": response})
    
    # Display response
    st.write("Response:", response)

# Display current session chat history (visible to everyone)
if st.session_state.chat_history:
    st.write("---")
    st.write("Current Session Chat History:")
    for chat in st.session_state.chat_history:
        st.write(f"Q: {chat['question']}")
        st.write(f"A: {chat['answer']}")
        st.write("---")

# Display available questions as examples
st.write("Sample Questions You Can Ask:")
for question in qa_pairs.keys():
    st.write(f"• {question}")

# Add password-protected access to saved chat history
st.write("---")
st.write("Admin Access - Saved Chat History:")

# Password input for admin access
admin_password = st.text_input("Enter admin password to view saved chat history:", type="password")

# Only show saved chat history if correct password is entered
if admin_password == st.secrets.get("ADMIN_PASSWORD", "default_password"):  # You'll need to set this in Streamlit secrets
    try:
        # Check if master log exists
        master_log = "chat_history/master_chat_log.txt"
        if os.path.exists(master_log):
            with open(master_log, "r", encoding="utf-8") as f:
                chat_contents = f.read()
                # Create download button
                st.download_button(
                    label="Download Complete Chat History",
                    data=chat_contents,
                    file_name="chat_history.txt",
                    mime="text/plain"
                )
                # Display the contents
                st.text_area("Complete Chat History", chat_contents, height=300)
        else:
            st.write("No saved chat history found yet.")
    except Exception as e:
        st.error(f"Error accessing chat history: {str(e)}")
elif admin_password:  # Only show error if they've tried to enter a password
    st.error("Incorrect password. Access denied.")

# Footer
st.write("---")
st.write("Thank you for exploring my background! Feel free to ask more questions.")
