# GlucoVision

**GlucoVision** is a state-of-the-art, AI-powered nutritional analysis platform designed to help individuals monitor and manage their glycaemic health. By leveraging advanced Natural Language Processing (NLP) and Retrieval-Augmented Generation (RAG), GlucoVision transforms simple meal logs into actionable, medical-grade dietary insights.

## Key Features

-   **AI-Powered Food Analysis**: Accurately extracts food items from natural language descriptions and matches them against a comprehensive database.
-   **Intelligent Risk Assessment**: Calculates total sugar, carbs, fiber, protein, and fat to assign a glycaemic risk level (Safe, Moderate, High).
-   **RAG-Enhanced Suggestions**: Generates science-backed, personalized dietary adjustments using LLMs (Groq).
-   **Comprehensive History**: Logs daily entries and visualizes weekly trends.

## Setup Instructions

### Prerequisites
-   Python 3.8+
-   `pip`

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/hegde-safal/glucovison.git
    cd glucovison
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Download NLP Models**
    ```bash
    python -m spacy download en_core_web_sm
    ```

4.  **Configure Environment**
    -   Create a `.env` file in the root directory.
    -   Add your Groq API key (optional, for AI suggestions):
        ```env
        GROQ_API_KEY=your_api_key_here
        ```

5.  **Run the Application**
    ```bash
    python app.py
    ```

6.  **Access the Dashboard**
    -   Open `http://localhost:5000` in your browser.

## Project Structure

```text
glucovison/
├── app/
│   ├── __init__.py      # App factory
│   ├── routes.py        # API endpoints
│   ├── rag.py           # RAG engine
│   ├── nlp.py           # NLP engine
│   ├── nutrition.py     # Nutrition logic
│   ├── storage.py       # DB manager
│   ├── static/          # Assets
│   └── templates/       # HTML templates
├── nutrition_master.csv # Food database
├── requirements.txt
└── app.py               # Entry point
```
