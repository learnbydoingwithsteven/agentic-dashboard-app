# Agentic Dashboard App

## Tech Stack Choices

### 🚀 Vite
- **Why Vite?**
  - **Instant Server Startup**: Leverages native ES modules for lightning-fast development server initialization.
  - **Hot Module Replacement (HMR)**: Updates components in real-time without full page reloads, improving developer productivity.
  - **Modern JS/TS Support**: Built-in out-of-the-box support for TypeScript, JSX, and CSS modules with no configuration required.
  - **Lightweight Build Process**: Avoids the complexity of traditional bundlers like Webpack, reducing build times and configuration overhead.
  - **Plugin Ecosystem**: Integrates seamlessly with tools like TypeScript, Prettier, and ESLint for a streamlined development workflow.

### 🧠 React
- **Why React?**
  - **Component-Based Architecture**: Enables reusable, modular UI components that simplify maintenance and scalability.
  - **Virtual DOM**: Optimizes DOM updates for better performance compared to direct DOM manipulation.
  - **TypeScript Integration**: Provides strong typing and tooling support for larger applications.
  - **Ecosystem & Community**: Access to a vast library of third-party packages (e.g., Redux, React Router) and a large developer community.
  - **Unidirectional Data Flow**: Simplifies state management and debugging through predictable data flow.

### 📊 Charting Style (Vega-Lite)
- **Why Vega-Lite?**
  - **Declarative Syntax**: Uses JSON specifications to define visualizations, making it easy to create and modify charts.
  - **Interactivity**: Supports dynamic, user-driven visualizations (e.g., tooltips, zooming, filtering).
  - **Flexibility**: Handles a wide range of chart types (bar, line, scatter, etc.) and can be customized with custom scales or encodings.
  - **Integration with React**: Seamless compatibility with React components for embedding visualizations directly into the UI.
  - **Performance**: Optimized for rendering large datasets efficiently.

## Project Structure

```
agentic_viz_app/
├── backend/                # Python backend (Flask)
│   ├── src/                # Source code
│   │   ├── agent_service.py  # Autogen agent logic
│   │   ├── main.py           # Flask API endpoints
│   │   └── uploads/          # Uploaded CSV files storage
│   ├── venv/                 # Python virtual environment
│   └── requirements.txt      # Backend dependencies
│
├── frontend/               # React frontend
│   ├── public/               # Static assets (e.g., favicon, index.html)
│   ├── src/                  # Application code
│   │   ├── app/              # Main application entry point
│   │   ├── components/       # Reusable UI components (e.g., charts, modals)
│   │   ├── lib/              # Utility functions (e.g., API helpers, data parsers)
│   │   └── ...               # Additional source files
│   ├── package.json          # Frontend dependencies
│   ├── pnpm-lock.yaml        # Dependency lock file
│   └── vite.config.ts        # Vite configuration
│
└── README.md                 # This file
```

## Key Features

- **AI-Driven Visualizations**:
  - **Automatic Insights**: Uses Autogen agents to analyze datasets and generate initial visualizations.
  - **Custom Prompts**: Allows users to define specific visualization requirements via natural language prompts.
  - **Multiple LLM Support**: Works with both Groq API and local Ollama models.
- **Interactive Dashboards**:
  - Built with Plotly for dynamic, user-friendly data exploration.
  - Supports real-time updates and agent monitoring during visualization generation.
  - Allows direct code execution for custom visualizations.
- **Modular Architecture**:
  - Clear separation of frontend (React) and backend (Flask) for maintainability.
  - Backend handles data processing and API logic, while the frontend focuses on UI/UX.
  - Secure code execution sandbox for running Python visualization code.
- **Scalability**:
  - Designed to handle large datasets (e.g., the 2015 Friuli-Venezia-Giulia public finance dataset).
  - Easily extendable to support additional data sources or visualization types.
  - Ability to cancel long-running agent jobs and reset the backend state.

## Setup and Running Locally

### Prerequisites
- Python 3.10+
- Node.js (with pnpm)
- Either:
  - Groq API Key (Get one from [https://console.groq.com/](https://console.groq.com/))
  - Ollama installed locally (Get it from [https://ollama.com/](https://ollama.com/))

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd agentic_viz_app/backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Unix/Mac
   venv\Scripts\activate    # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up the model provider:
   - For Groq:
     ```bash
     export GROQ_API_KEY=your_api_key_here
     ```
   - For Ollama:
     - Make sure Ollama is running locally
     - No environment variables needed - the app will detect Ollama automatically

5. Run the backend server:
   ```bash
   python src/main.py
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd agentic_viz_app/frontend
   ```
2. Install dependencies:
   ```bash
   pnpm install
   ```
3. Start the development server:
   ```bash
   pnpm dev
   ```

> ⚠️ Ensure both backend (http://localhost:5001) and frontend (http://localhost:5173) are running simultaneously.
