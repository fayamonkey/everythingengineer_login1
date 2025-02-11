import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import os
import bcrypt
from pathlib import Path
from datetime import datetime
import json

# Initialize session state for invite codes if not exists
if 'invite_codes' not in st.session_state:
    st.session_state.invite_codes = {}
    # Load initial codes from secrets
    for code, used in st.secrets.get('invite_codes', {}).items():
        st.session_state.invite_codes[code] = {
            'used': used,
            'created_by': 'admin',
            'used_by': None,
            'used_at': None
        }

def is_admin(email):
    """Check if the user is an admin"""
    admin_emails = st.secrets.get('admin_users', {}).get('admin_emails', [])
    return email in admin_emails

def generate_invite_code(admin_email):
    """Generate a new invite code"""
    if not is_admin(admin_email):
        return False, "Not authorized to generate invite codes"
    
    # Generate a new code (format: BETA + 3-digit number)
    existing_codes = list(st.session_state.invite_codes.keys())
    max_num = 0
    for code in existing_codes:
        if code.startswith('BETA'):
            try:
                num = int(code[4:])
                max_num = max(max_num, num)
            except ValueError:
                continue
    
    new_code = f"BETA{(max_num + 1):03d}"
    st.session_state.invite_codes[new_code] = {
        'used': False,
        'created_by': admin_email,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'used_by': None,
        'used_at': None
    }
    
    return True, new_code

def validate_invite_code(code):
    """Check if an invite code is valid and unused"""
    return (code in st.session_state.invite_codes and 
            not st.session_state.invite_codes[code]['used'])

def mark_invite_code_used(code, email):
    """Mark an invite code as used"""
    if code in st.session_state.invite_codes:
        st.session_state.invite_codes[code]['used'] = True
        st.session_state.invite_codes[code]['used_by'] = email
        st.session_state.invite_codes[code]['used_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Initialize Brevo (Sendinblue) configuration
def init_brevo():
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = st.secrets["BREVO_API_KEY"]
    return sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

# Send verification email
def send_verification_email(email, verification_code):
    try:
        api_instance = init_brevo()
        
        # Use your verified email in Brevo
        sender = {"email": "fayamonkeyrecords@gmail.com", "name": "AI Engineering"}
        to = [{"email": email}]
        
        html_content = f"""
        <html>
            <body>
                <h2>Welcome to CustomGPT Creator!</h2>
                <p>Thank you for registering. To complete your registration, please enter this verification code in the application:</p>
                <h3 style="background-color: #f0f0f0; padding: 10px; text-align: center; font-size: 24px;">{verification_code}</h3>
                <p>If you didn't request this verification code, please ignore this email.</p>
                <p>Best regards,<br>AI Engineering Team</p>
            </body>
        </html>
        """
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=to,
            sender=sender,
            subject="Verify your CustomGPT Creator account",
            html_content=html_content
        )
        
        # Send email and get response
        response = api_instance.send_transac_email(send_smtp_email)
        st.write(f"Email sent successfully! Please check your inbox (and spam folder).")
        return True
    except ApiException as e:
        error_message = f"Error sending email: {str(e)}"
        if "sender not allowed" in str(e).lower():
            error_message = "Sender email not verified in Brevo. Please verify your sender email in the Brevo dashboard."
        elif "invalid api key" in str(e).lower():
            error_message = "Invalid Brevo API key. Please check your API key configuration."
        st.error(error_message)
        return False
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return False

# User management functions
def get_user_data():
    """Get user data from session state"""
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {'usernames': {}}
    return st.session_state.user_data

def save_user_data(users):
    """Save user data to session state"""
    st.session_state.user_data = users

def register_user(email, password, name, invite_code):
    # First check if invite code is valid
    if not validate_invite_code(invite_code):
        return False, "Invalid or already used invite code"

    users = get_user_data()
    
    if email in users["usernames"]:
        return False, "Email already registered"
    
    # Generate verification code
    verification_code = str(hash(email + str(os.urandom(32))))[:6]
    
    # Hash password
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    # Add user to database
    users["usernames"][email] = {
        "name": name,
        "password": hashed_password,
        "verified": False,
        "verification_code": verification_code,
        "invite_code": invite_code,
        "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    save_user_data(users)
    
    # Mark invite code as used
    mark_invite_code_used(invite_code, email)
    
    # Send verification email
    if send_verification_email(email, verification_code):
        return True, "Registration successful. Please check your email for verification code."
    return False, "Failed to send verification email"

def verify_email(email, code):
    users = get_user_data()
    
    if email not in users["usernames"]:
        return False, "User not found"
    
    user = users["usernames"][email]
    if user["verification_code"] == code:
        user["verified"] = True
        save_user_data(users)
        return True, "Email verified successfully"
    
    return False, "Invalid verification code"

def authenticate_user(email, password):
    users = get_user_data()
    
    if email not in users["usernames"]:
        return False, "Invalid email or password"
    
    user = users["usernames"][email]
    if not user["verified"]:
        return False, "Please verify your email first"
    
    if bcrypt.checkpw(password.encode(), user["password"].encode()):
        return True, user["name"]
    
    return False, "Invalid email or password" 