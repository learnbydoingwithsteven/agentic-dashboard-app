# Agentic Dashboard App

<div align="center">
  <img src="https://i.imgur.com/placeholder.png" alt="Agentic Dashboard App" width="800"/>
  <br>
  <a href="https://github.com/learnbydoingwithsteven/agentic-dashboard-app/stargazers"><img src="https://img.shields.io/github/stars/learnbydoingwithsteven/agentic-dashboard-app" alt="Stars Badge"/></a>
  <a href="https://github.com/learnbydoingwithsteven/agentic-dashboard-app/network/members"><img src="https://img.shields.io/github/forks/learnbydoingwithsteven/agentic-dashboard-app" alt="Forks Badge"/></a>
  <a href="https://github.com/learnbydoingwithsteven/agentic-dashboard-app/pulls"><img src="https://img.shields.io/github/issues-pr/learnbydoingwithsteven/agentic-dashboard-app" alt="Pull Requests Badge"/></a>
  <a href="https://github.com/learnbydoingwithsteven/agentic-dashboard-app/issues"><img src="https://img.shields.io/github/issues/learnbydoingwithsteven/agentic-dashboard-app" alt="Issues Badge"/></a>
  <a href="https://github.com/learnbydoingwithsteven/agentic-dashboard-app/blob/main/LICENSE"><img src="https://img.shields.io/github/license/learnbydoingwithsteven/agentic-dashboard-app" alt="License Badge"/></a>
</div>

> An AI-powered data visualization platform that uses LLM agents to automatically generate insightful visualizations from your datasets.

## 🌟 Overview

The Agentic Dashboard App is a cutting-edge platform that combines the power of Large Language Models (LLMs) with data visualization to help users gain insights from their data without extensive coding or data science expertise. The application uses a team of specialized AI agents to analyze datasets, identify patterns, and generate meaningful visualizations.

### Key Differentiators

- **AI-First Approach**: Uses a team of specialized LLM agents (analyst, coder, manager) to collaboratively generate visualizations
- **Flexible LLM Integration**: Works with both cloud-based LLMs (Groq) and local models (Ollama)
- **Real-time Agent Monitoring**: Watch the agents' thought process as they analyze your data
- **Code Execution**: Secure sandbox for executing Python visualization code
- **Interactive UI**: Modern, responsive interface with real-time updates

## 🛠️ Tech Stack

### Frontend
- **React 18** with **TypeScript** for type-safe component development
- **Vite** for lightning-fast development and optimized builds
- **TailwindCSS** with **shadcn/ui** for beautiful, responsive UI components
- **Plotly.js** for interactive, publication-quality visualizations
- **React Query** for efficient server state management

### Backend
- **Flask** for a lightweight, flexible API server
- **Autogen** framework for creating and orchestrating LLM agents
- **Groq Client** for accessing cloud-based LLMs
- **Ollama Integration** for running models locally
- **Pandas** for powerful data manipulation and analysis

## 📂 Project Structure

```
agentic-dashboard-app/
├── backend/                # Python backend (Flask)
│   ├── src/                # Source code
│   │   ├── agent_service.py      # Autogen agent orchestration
│   │   ├── api_key_middleware.py # API key validation
│   │   ├── code_execution_service.py # Secure Python code execution
│   │   ├── main.py               # Flask API endpoints
│   │   ├── ollama_config.py      # Ollama integration
│   │   └── uploads/              # Uploaded datasets storage
│   └── requirements.txt          # Backend dependencies
│
├── frontend/               # React frontend (TypeScript)
│   ├── public/             # Static assets
│   ├── src/                # Application code
│   │   ├── app/            # Main application components
│   │   ├── components/     # Reusable UI components
│   │   │   ├── ui/         # Base UI components (shadcn/ui)
│   │   │   ├── AgentConversationMonitor.tsx # Real-time agent logs
│   │   │   ├── ApiKeySettings.tsx # API key management
│   │   │   ├── CodeVisualization.tsx # Code execution results
│   │   │   └── ...         # Other components
│   │   ├── lib/            # Utility functions
│   │   └── ...             # Additional source files
│   ├── package.json        # Frontend dependencies
│   └── vite.config.ts      # Vite configuration
│
└── README.md               # Project documentation
```

## ✨ Features

### 🤖 AI Agent System

The application uses a team of specialized AI agents to analyze data and generate visualizations:

- **Data Analyst Agent**: Examines the dataset and identifies meaningful patterns and insights
- **Visualization Coder Agent**: Translates insights into Python code using Plotly
- **Manager Agent**: Coordinates the workflow between agents and ensures quality output

### 📊 Visualization Capabilities

- **Automatic Visualization Generation**: Get instant insights without writing code
- **Natural Language Prompts**: Request specific visualizations using plain English
- **Custom Code Execution**: Write and execute your own Python visualization code
- **Interactive Plots**: Explore data with interactive Plotly visualizations

### 🔄 Workflow

1. **Upload Dataset**: CSV files with tabular data
2. **Configure API**: Choose between Groq API or local Ollama models
3. **Generate Visualizations**: Automatically or with custom prompts
4. **Monitor Progress**: Watch the agents' thought process in real-time
5. **Explore Results**: Interact with the generated visualizations

### 🛡️ Security & Performance

- **Secure Code Execution**: Sandboxed environment for running Python code
- **Efficient Data Processing**: Optimized for handling large datasets
- **Job Control**: Cancel long-running jobs and reset the system state
- **Model Flexibility**: Switch between cloud and local models as needed

## 🚀 Installation & Setup

### Prerequisites

- **Python 3.10+** - For the backend server
- **Node.js 18+** - For the frontend application
- **pnpm** - Package manager for the frontend
- **One of the following**:
  - **Groq API Key** - Get one from [Groq Console](https://console.groq.com/)
  - **Ollama** - Install from [ollama.com](https://ollama.com/) and pull models like `ollama pull llama3`

### Backend Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/learnbydoingwithsteven/agentic-dashboard-app.git
   cd agentic-dashboard-app
   ```

2. **Set up Python environment**:
   ```bash
   cd backend
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure LLM provider**:

   **Option 1: Groq API**
   ```bash
   # On Windows (PowerShell)
   $env:GROQ_API_KEY = "your_groq_api_key_here"

   # On macOS/Linux
   export GROQ_API_KEY=your_groq_api_key_here
   ```

   **Option 2: Ollama**
   - Ensure Ollama is installed and running
   - Pull models you want to use: `ollama pull llama3`
   - No environment variables needed - the app will detect Ollama automatically

5. **Start the backend server**:
   ```bash
   python src/main.py
   ```
   The server will run on http://localhost:5001

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd ../frontend
   ```

2. **Install dependencies**:
   ```bash
   pnpm install
   ```

3. **Start the development server**:
   ```bash
   pnpm dev
   ```
   The frontend will be available at http://localhost:5173

## 🧪 Usage Guide

1. **Open the application** in your browser at http://localhost:5173

2. **Configure API Settings**:
   - Choose between Groq API or Ollama
   - If using Groq, enter your API key
   - Click "Save & Validate" to verify your settings

3. **Upload a Dataset**:
   - Click "Choose File" to select a CSV file
   - The app comes with a sample Italian public finance dataset if you don't have one

4. **Generate Visualizations**:
   - Click "Generate Visualizations" for automatic analysis
   - Or enter a specific prompt like "Show me a comparison of total commitments by province"
   - Watch the agent conversation in real-time on the right panel

5. **Explore Results**:
   - Interact with the generated visualizations
   - Hover over data points for more information
   - Try different prompts to explore various aspects of your data

6. **Advanced Features**:
   - Use the "Execute Code" feature to run custom Python visualization code
   - Click "Reset Backend" if you want to start fresh
   - Cancel long-running jobs with the "Cancel" button

## 🔧 Troubleshooting

### Common Issues

#### Backend Issues

- **"API key is required" error**: Make sure you've entered a valid Groq API key or selected Ollama as your provider
- **"No models found" error**: Ensure Ollama is running if you're using it as your provider
- **Visualization generation fails**: Check the agent logs for specific error messages

#### Frontend Issues

- **"picomatch" dependency error**: Run `pnpm install` again to resolve dependency issues
- **Cannot switch from Ollama back to Groq**: Use the "Reset Backend" button and then configure your Groq API key
- **Blank visualization**: Check the error message in the visualization panel and adjust your prompt

### Debugging Tips

1. **Check the backend logs**: Look for error messages in the terminal where the backend is running
2. **Inspect network requests**: Use browser developer tools to check API responses
3. **Reset the backend**: Use the "Reset Backend" button to clear any stale state
4. **Restart both servers**: Sometimes a clean restart resolves issues

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add some amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines

- Follow the existing code style and organization
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting a PR

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Autogen](https://github.com/microsoft/autogen) for the multi-agent framework
- [Groq](https://groq.com/) for their fast LLM API
- [Ollama](https://ollama.com/) for making local LLMs accessible
- [Plotly](https://plotly.com/) for the interactive visualization library
- [React](https://reactjs.org/) and [Vite](https://vitejs.dev/) for the frontend framework

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/learnbydoingwithsteven">Learn By Doing With Steven</a>
</p>
