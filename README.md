# Bird Quiz

A web-based bird identification practice application that tests your ability to identify birds. You can choose from premade lists of birds or paste your own list. Once a list is selected, the app displays images of a random bird seleted from the list and then presents 4 options (1 correct answer + 3 similar-looking birds as determined by Azure OpenAI GPT-4) and asks you to choose the correct name, helping you reinforce your bird ID skills.

## Features

- **Custom bird lists**: Load your own list of birds you want to be quized on, one per line using their common name
- **Real bird images**: Fetches actual images from Wikimedia Commons
- **AI-powered options**: Uses Azure OpenAI GPT-4 to suggest similar-looking birds as wrong answers
- **Session scoring**: Tracks correct and incorrect answers during your session
- **Immediate feedback**: Know if you're right or wrong after each guess, with a link to the bird's Wikipedia page when you miss one
- **Simple UI**: Clean, minimal design focused on learning
- **Azure OpenAI AD authentication**: Secure authentication for Azure OpenAI (no API keys needed)

## Prerequisites

### 1. Python 3.10+
Ensure you have Python installed:
```bash
python --version
```

### 2. Azure OpenAI Access
You need an Azure OpenAI deployment with a GPT-4 (or any other capable) model. You will need the following:
- **Azure OpenAI Endpoint**: `https://your-resource-name.openai.azure.com/`
- **Deployment Name**: The name of your GPT-4 deployment (e.g., `gpt-4`)
- **Azure Subscription**: Access to the Azure subscription where the resource is deployed

### 3. Azure CLI (for AD authentication)
Install Azure CLI if you don't have it:
- [Azure CLI Installation Guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)

### 4. Authenticate with Azure
Before running the app, authenticate with your Azure account:
```bash
az login
```
This will open a browser window for you to sign in with your Azure AD credentials. The app will now access Azure Open AI as you.

## Setup Instructions

### 1. Clone or Download the Project
```bash
git clone https://github.com/ssemyan/BirdQuiz
```

### 2. Create a Python Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Edit `.env` and add your Azure OpenAI details:
```
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
```

**Note**: No API key is needed! The app uses Azure AD authentication via `az login`.


## Running the App

### 1. Activate Virtual Environment
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Start the Flask Server
```bash
python app.py
```

You should see output like:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### 3. Open in Browser
Open your web browser and navigate to:
```
http://localhost:5000
```

### 4. Pick a Bird List
1. Pick one of the premade lists or click Custom to paste your own list
2. The quiz will start automatically

### 5. Answer Questions
- Look at the bird image
- Select one of the 4 options
- Get immediate feedback (correct or incorrect)
- Your score updates in real-time
- Click "Next Question" to continue
- To load a different list, click the hamburger icon in the upper right and select 'Load Different Birds'

### 6. Stop the Server
Press `Ctrl+C` in the terminal to stop the Flask server.

## How It Works

1. **Load Birds**: App loads from a premade file or a pasted list
2. **Pick Random Bird**: A random bird is selected for the quiz
3. **Fetch Image**: Real bird images are fetched from Wikimedia Commons API
4. **Generate Options**: Azure OpenAI GPT-4 suggests 3 similar-looking birds as wrong answers
5. **Present Quiz**: Images and 4 options are shown to you
6. **Score**: Your answer is checked and score is updated
7. **Repeat**: Process continues with new random birds

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Yes | Your Azure OpenAI resource endpoint |
| `AZURE_OPENAI_API_VERSION` | No | API version (default: `2024-02-01`) |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Yes | Your GPT-4 deployment name |

## Troubleshooting

### "Resource not found" Error
- Verify your Azure OpenAI endpoint is correct (should end with `/`)
- Make sure the deployment name matches your Azure portal
- Check that you have access to the resource: `az account show`

### "Not authenticated" Error
- Run `az login` to authenticate with Azure
- Make sure to use an Azure AD account with access to the OpenAI resource

### No bird images appearing
- The app tries to fetch from Wikimedia Commons
- If images aren't available for a bird, fallback message displays
- This is normal for less common bird species

### "No birds loaded" Error
- Verify the list file path is correct
- Check that the list isn't empty

## Project Structure

```
BirdFind/
├── app.py                          # Flask backend
├── requirements.txt                # Python dependencies
├── .env.example                    # Sample Environment variables
├── README.md                       # This file
├── [birdlist].txt                  # premade bird lists (one bird per line)
├── templates/
│   └── index.html                 # Frontend (HTML)
└── static/
    ├── favicon.svg                # App favicon
    └── *.css, *.js                # Frontend (static files)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve the main HTML page |
| `/api/load-birds` | POST | Load birds from a server file or pasted list |
| `/api/quiz-question` | GET | Get a new quiz question with options |

Example request bodies for `/api/load-birds`:

Load a premade list file:
```
{ "file_path": "wa_birds.txt" }
```

Load a pasted list:
```
{ "bird_names": "Cedar Waxwing\nGreat Egret\nBald Eagle" }
```

## Technologies Used

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript
- **AI**: Azure OpenAI (GPT-4)
- **Authentication**: Azure AD (DefaultAzureCredential)
- **Images**: Wikimedia Commons API
- **Data**: Plain text lists

## Notes

- Score tracking is per-session only (resets on page refresh or new list load)
- The app runs in debug mode by default (development only)
- For production, use a proper WSGI server (Gunicorn, uWSGI, etc.)
- Azure OpenAI API calls may incur charges based on your usage

## License

This project is for educational purposes and covered by the MIT license

## Support

For issues with Azure OpenAI setup, see: https://learn.microsoft.com/en-us/azure/ai-services/openai/
