import streamlit as st
import difflib
from openai import OpenAI
import PyPDF2
import os
from datetime import datetime
from gmail_utils import get_gmail_service, send_email

# Configure OpenAI API
if 'OPENAI_API_KEY' not in st.secrets:
    st.error("Please set your OpenAI API key in Streamlit secrets!")
    st.stop()

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])

# Initialize Gmail service
try:
    gmail_service = get_gmail_service()
except Exception as e:
    st.error(f"Error initializing Gmail service: {e}")
    gmail_service = None

def read_pdf_file(file_path, file_type):
    if not os.path.exists(file_path):
        st.error(f"{file_type} file not found at {file_path}")
        return None
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

def send_chat_summary(question, answer):
    """Send chat summary via email"""
    if not gmail_service:
        return
        
    try:
        recipient_email = st.secrets["RECIPIENT_EMAIL"]
        subject = f"Chat Interaction Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        body = f"""
New Chat Interaction:
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Question: {question}

Answer: {answer}

-------------------
"""
        send_email(gmail_service, recipient_email, subject, body)
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")

# Read both PDF files
resume_content = read_pdf_file("resume.pdf", "resume")
about_me_content = read_pdf_file("About Me.pdf", "About Me document")

if resume_content is None or about_me_content is None:
    st.error("Required PDF files not found or couldn't be read. Please ensure both resume.pdf and About Me.pdf are in the same directory.")
    st.stop()

# Title
st.title("Ask Me Anything - Kunal's AMA Agent")

# Intro
st.write("""
Welcome! This is Kunal's interactive AI Agent designed to help you learn about my background, expertise, and vision for Generative AI's impact on the world, especially in Enterprise Business. 

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
        system_prompt = f"""You are Kunal, a GenAI expert helping enterprises define and drive AI strategies, and you are eager to lead AI initiatives at VSP Vision's Global Innovation Center. 
You are approachable, insightful, and forward-thinking, with a talent for simplifying complex AI concepts to help others succeed. 
You are driven by a passion for leveraging AI to transform businesses and improve lives.  

Your mission in this AMA is to:  
1. Share insights grounded in your experience and expertise.  
2. Offer practical strategies for building AI-native frameworks and applications.  
3. Highlight the transformative potential of AI, particularly in vision care and enterprise operations.  
4. Inspire curiosity and deeper exploration of AI possibilities.  

Your responses should be based STRICTLY on the following documents and nothing else:  
---  
**Key Perspectives on AI and Enterprise Transformation:**  
Generative AI is redefining software development, shifting from rigid GUIs to adaptive, conversational UIs focused on real business value.  
Legacy methods like Agile/SAFe struggle to keep pace with LLM-enabled applications that learn and adapt in real time.  
Organizations must rethink tech stacks, operating models, development cycles, and metrics to transition into AI-native frameworks.  
The biggest barrier? Bridging the knowledge gap—especially between technical teams and business leaders unsure where to start or how to measure success.  

---  
**Resume Information:**  
{resume_content}  

**Background Information:**  
{about_me_content}  

---  
**Rules and Boundaries:**  
1. Only provide information explicitly mentioned in the documents above.  
2. If asked about topics outside the documents, respond: \"I don't have that information in my background documents.\"  
3. Keep responses concise, professional, and engaging.  
4. Avoid assumptions or adding details not present in the documents.  
5. For opinions or future vision questions, tie them to the expertise shown in the documents.  

**Proactive Engagement Guidelines:**  
- Ask clarifying questions if a query seems vague or could benefit from deeper exploration.  
- Provide examples or frameworks to illustrate AI strategies when relevant.  
- Invite follow-up questions to encourage deeper discussions.  

**Example Prompt Responses:**  
- \"That's a great question! Based on my background, one approach is...\"  
- \"While I can't speak to specifics outside the provided documents, a general principle in AI adoption is...\"  
- \"How do you see AI enhancing workflows in your organization? I'd be happy to explore that further.\"  
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

# Initialize session state variables
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'last_question' not in st.session_state:
    st.session_state.last_question = None
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""

def clear_input():
    st.session_state.user_input = ""

# Create a form for user input
with st.form(key='question_form'):
    user_input = st.text_input(
        "Ask me anything about my career journey:",
        key='user_input',
        value=st.session_state.user_input,
        on_change=clear_input
    ).strip()
    submit_button = st.form_submit_button("Ask")

if submit_button:
    if not user_input:
        st.warning("Please enter a question before submitting.")
    else:
        try:
            # Save the question to prevent duplicates
            if user_input == st.session_state.last_question:
                st.warning("You just asked this question. Try asking something else!")
            else:
                st.session_state.last_question = user_input
                
                # Get AI response
                response = get_gpt4_response(user_input)
                
                # Display the response
                st.write("Response:", response)
                
                # Save chat history first
                st.session_state.chat_history.append({"question": user_input, "answer": response})
                save_chat_history(user_input, response)
                append_to_master_log(user_input, response)
                
                # Clear the input field
                st.session_state.user_input = ""
                
                # Then try to send email if Gmail service is available
                if gmail_service:
                    try:
                        email_body = "Recent Chat:\n\n"
                        email_body += f"Q: {user_input}\nA: {response}\n"
                        send_email(
                            gmail_service,
                            st.secrets["RECIPIENT_EMAIL"],
                            "New Chat Interaction",
                            email_body
                        )
                    except Exception as e:
                        st.error(f"Failed to send email notification: {e}")
                        # Email failure doesn't affect the chat functionality
                
        except Exception as e:
            st.error(f"Error processing your question: {str(e)}")

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
