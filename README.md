# CustomGPT Creator

A Streamlit application that helps create custom GPT instructions with user authentication.

## Security and Setup

### API Keys Setup
1. Copy the template secrets file:
   ```bash
   cp .streamlit/secrets.example.toml .streamlit/secrets.toml
   ```
2. Edit `.streamlit/secrets.toml` and add your actual API keys:
   - Get your OpenAI API key from: https://platform.openai.com/api-keys
   - Get your Brevo API key from: https://app.brevo.com/settings/keys/api

⚠️ IMPORTANT: Never commit the actual `secrets.toml` file to Git. It's already in `.gitignore` for your security.

### For Local Development
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set up your secrets.toml as described above
3. Run the application:
   ```bash
   streamlit run app.py
   ```

### For Deployment
When deploying to platforms like Streamlit Cloud:
1. Never expose your `secrets.toml` file
2. Add your API keys through the platform's secure secrets management:
   - For Streamlit Cloud: Add them in the app's settings under "Secrets"
   - The format should match the structure in `secrets.example.toml`

### Security Features
- User authentication with email verification
- Secure password hashing using bcrypt
- API keys stored securely in `secrets.toml` (not in Git)
- User data stored in `users.yaml` (not in Git)
- Email verification using Brevo
- Session management using Streamlit's secure session state

## Files Not to Commit
The following files are in `.gitignore` and should never be committed:
- `.streamlit/secrets.toml` (contains API keys)
- `users.yaml` (contains user data)
- `__pycache__/` and `*.pyc` (Python cache files)

## Contributing
1. Fork the repository
2. Create your feature branch
3. Make your changes
4. Submit a pull request

## License
[Add your chosen license here]

## Features

- Interactive chat interface
- Step-by-step guidance through the CustomGPT creation process
- Integration with OpenAI's GPT-4 Turbo model
- Export results as Markdown files
- Save and manage multiple CustomGPT results
- Corporate branding and professional interface

## Deployment on Streamlit Cloud

1. Fork this repository to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy your app by connecting to your GitHub repository
4. In your app's settings on Streamlit Cloud, add your OpenAI API key in the Secrets section:
   ```toml
   OPENAI_API_KEY = "your-api-key-here"
   ```

## Local Development

1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.streamlit/secrets.toml` file in your project directory:
   ```toml
   OPENAI_API_KEY = "your-api-key-here"
   ```
4. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

## Usage

1. The app will guide you through the process of creating a CustomGPT
2. Your results will be saved in the sidebar
3. You can download results as Markdown (.md) files
4. Use "Clear Chat" to start a new conversation
5. Use "Clear Results" to remove saved results

## Requirements

- Python 3.8 or higher
- OpenAI API key
- Internet connection

## Note

Make sure to keep your OpenAI API key secure and never commit it to version control. 