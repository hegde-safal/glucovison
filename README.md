# GlucoVision

**GlucoVision** is a state-of-the-art, AI-powered nutritional analysis platform designed to help individuals monitor and manage their glycaemic health. By leveraging advanced Natural Language Processing (NLP) and Retrieval-Augmented Generation (RAG), GlucoVision transforms simple meal logs into actionable, medical-grade dietary insights.

## Key Features

-   **Medical-Grade Interface**: A clean, accessible, and responsive UI designed for clarity and ease of use.
-   **AI-Powered Food Analysis**:
    -   **NLP Parsing**: Accurately extracts food items from natural language descriptions (e.g., "I had a bowl of oatmeal with blueberries").
    -   **Fuzzy Matching**: Matches inputs against a master database of over 6,000 food items for precise nutritional data.
-   **Intelligent Risk Assessment**:
    -   Calculates total sugar, carbs, fiber, protein, and fat.
    -   Assigns a glycaemic risk level (Safe, Moderate, High) based on WHO-aligned thresholds.
-   **RAG-Enhanced Suggestions**:
    -   Uses a localized RAG pipeline to generate science-backed, personalized dietary adjustments for the next day.
    -   Suggestions are context-aware, correcting specific nutrient imbalances.
-   **Comprehensive History**:
    -   **Daily Logging**: Automatically saves meal data and analysis results to a secure local database.
    -   **Weekly Analytics**: Visualizes nutritional trends over time to identify patterns.
-   **Privacy-First Approach**: All personal data and history are stored locally on the user's machine.

## Technology Stack

-   **Backend**: Python (Flask)
-   **Frontend**: HTML5, CSS3, JavaScript (Vanilla), Chart.js
-   **Database**: SQLite
-   **AI & NLP**:
    -   `spacy` for natural language parsing
    -   `rapidfuzz` for database matching
    -   `groq` (Optional) for LLM-powered suggestions

## Setup Instructions

### Prerequisites
-   Python 3.8+
-   `pip` (Python package manager)

### Installation

1.  **Clone the Repository**
    ```bash
    git clone <repository_url>
    cd phase1_app
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Download NLP Models**
    ```bash
    python -m spacy download en_core_web_sm
    ```

4.  **Configure Environment (Optional for AI)**
    -   Create a `.env` file in the root directory.
    -   Add your Groq API key:
        ```env
        GROQ_API_KEY=your_api_key_here
        ```
    -   *Note: The app runs without an API key using mock suggestions.*

5.  **Run the Application**
    ```bash
    python app.py
    ```

6.  **Access the Dashboard**
    -   Open your browser and navigate to: `http://localhost:5000`

## Project Structure

```text
phase1_app/
├── app/
│   ├── __init__.py      # App factory and configuration
│   ├── routes.py        # Web routes and API endpoints
│   ├── rag.py           # AI/RAG engine for suggestions
│   ├── storage.py       # SQLite database manager
│   ├── static/          # CSS, JS, and images
│   └── templates/       # HTML templates
├── nutrition.db         # Local SQLite database (auto-generated)
├── nutrition_master.csv # Food database
├── .env                 # Environment variables
├── requirements.txt     # Python dependencies
└── app.py               # Application entry point
```

---
*Disclaimer: GlucoVision is a wellness tool and is not intended to replace professional medical advice, diagnosis, or treatment.*
