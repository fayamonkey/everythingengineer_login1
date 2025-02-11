import streamlit as st
import openai
from pathlib import Path
import json
from datetime import datetime
import os
from auth import authenticate_user, register_user, verify_email, is_admin, generate_invite_code

# Set OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "results" not in st.session_state:
    st.session_state.results = {}
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "registration_status" not in st.session_state:
    st.session_state.registration_status = None
if "needs_verification" not in st.session_state:
    st.session_state.needs_verification = False
if "verification_email" not in st.session_state:
    st.session_state.verification_email = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# Set up the page
st.set_page_config(page_title="CustomGPT Creator", page_icon="🤖", layout="wide")

def login_form():
    st.subheader("Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login"):
        success, result = authenticate_user(email, password)
        if success:
            st.session_state.authenticated = True
            st.session_state.user_name = result
            st.session_state.user_email = email  # Store email for admin check
            st.rerun()
        else:
            st.error(result)

def registration_form():
    st.subheader("Register")
    name = st.text_input("Name", key="reg_name")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_password")
    invite_code = st.text_input("Invite Code", key="invite_code")
    
    if st.button("Register"):
        if name and email and password and invite_code:
            success, message = register_user(email, password, name, invite_code)
            if success:
                st.session_state.needs_verification = True
                st.session_state.verification_email = email
                st.success(message)
            else:
                st.error(message)
        else:
            st.error("Please fill in all fields")

def verification_form():
    st.subheader("Verify Email")
    code = st.text_input("Enter verification code")
    
    if st.button("Verify"):
        success, message = verify_email(st.session_state.verification_email, code)
        if success:
            st.session_state.needs_verification = False
            st.session_state.verification_email = None
            st.success(message)
            st.rerun()
        else:
            st.error(message)

# Function to load system prompt
def load_system_prompt():
    try:
        with open("systemprompt.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        st.error("System prompt file (systemprompt.md) not found!")
        return None

# Function to generate response
def generate_response(messages):
    try:
        response = openai.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=messages,
            temperature=0.7,
            max_tokens=4000,
            stream=True
        )
        
        # Initialize empty string for the response
        full_response = ""
        message_placeholder = st.empty()
        
        # Stream the response
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                full_response += chunk.choices[0].delta.content
                message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)
        return full_response
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return None

def show_admin_interface(email):
    """Show admin interface if user is admin"""
    if is_admin(email):
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Admin Panel")
        
        # Generate new invite code
        if st.sidebar.button("Generate New Invite Code"):
            success, result = generate_invite_code(email)
            if success:
                st.sidebar.success(f"New invite code generated: {result}")
            else:
                st.sidebar.error(result)
        
        # Show all invite codes
        st.sidebar.markdown("### Invite Codes")
        for code, details in st.session_state.invite_codes.items():
            with st.sidebar.expander(f"Code: {code}"):
                st.write(f"Used: {details['used']}")
                if details['used']:
                    st.write(f"Used by: {details['used_by']}")
                    st.write(f"Used at: {details['used_at']}")
                st.write(f"Created by: {details['created_by']}")
                if 'created_at' in details:
                    st.write(f"Created at: {details['created_at']}")

# Main app layout
if not st.session_state.authenticated:
    st.title("Welcome to CustomGPT Creator")
    st.write("Please login or register to continue.")
    
    # Create two columns for login and registration
    if st.session_state.needs_verification:
        verification_form()
    else:
        col1, col2 = st.columns(2)
        with col1:
            login_form()
        with col2:
            registration_form()
else:
    # Create two columns - one for the sidebar content and one for the main chat
    sidebar_col, main_col = st.columns([1, 3])

    with main_col:
        st.title(f"Welcome {st.session_state.user_name} to CustomGPT Creator")
        
        # Only show chat interface when authenticated
        if openai.api_key:
            # Load system prompt
            system_prompt = load_system_prompt()
            
            if system_prompt:
                # Display chat messages
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
                
                # Chat input
                if prompt := st.chat_input("What kind of CustomGPT would you like to create?"):
                    # Add user message to chat
                    st.chat_message("user").markdown(prompt)
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    
                    # Generate response
                    with st.chat_message("assistant"):
                        messages = [
                            {"role": "system", "content": system_prompt},
                            *st.session_state.messages
                        ]
                        response = generate_response(messages)
                        if response:
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            
                            # Save first response of each chat as a result
                            if len(st.session_state.messages) == 2:  # First response (after user's first message)
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                st.session_state.results[timestamp] = response
        else:
            st.warning("Please enter your OpenAI API key in the sidebar to start.")

    # Sidebar
    with sidebar_col:
        # Load and display local image
        st.sidebar.image("everythingengineer.png", use_container_width=True)
        
        # Corporate information
        st.sidebar.markdown("""
        ### Created by
        **Dirk Wonhoefer**  
        AI Engineering  
        [dirk.wonhoefer@ai-engineering.ai](mailto:dirk.wonhoefer@ai-engineering.ai)  
        [ai-engineering.ai](https://ai-engineering.ai)
        """)
        
        st.sidebar.markdown("""
        ### About
        EXAMPLE PROMPT: A customGPT that helps me to create a business plan for my business ideas.
                """)
        
        # Results section
        st.sidebar.markdown("### Your CustomGPT Results")
        
        # Display saved results with download buttons
        for timestamp, result in st.session_state.results.items():
            with st.sidebar.expander(f"Result from {timestamp}"):
                st.markdown(result[:200] + "..." if len(result) > 200 else result)
                
                # Markdown download
                md_filename = f"CustomGPT_Instructions_{timestamp}.md"
                st.download_button(
                    "Download as Markdown",
                    result,
                    file_name=md_filename,
                    mime="text/markdown"
                )
        
        # Clear buttons
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Clear Chat"):
                st.session_state.messages = []
                st.rerun()
        with col2:
            if st.button("Clear Results"):
                st.session_state.results = {}
                st.rerun()
        
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_name = None
            st.rerun()

        if st.sidebar.button("Start New Chat"):
            st.session_state.messages = []
            st.rerun()

    # Add this line after successful authentication
    show_admin_interface(st.session_state.get('user_email')) 