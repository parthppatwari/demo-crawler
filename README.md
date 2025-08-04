# 📍 Smart Local Search with Email Extraction

This project is a **Streamlit-based web app** that helps you search for local services using natural language, enhances your query for accurate Google Maps searches, and extracts business email IDs from their websites.

## 🚀 Features

- 🔤 **Prompt Correction**: Uses Together.ai's Mistral model to improve your input prompt for better search accuracy.
- 📍 **Location Search**: Uses the SearchAPI to find relevant local results.
- 🕸️ **Website Scraping**: Extracts email IDs from business websites using OpenAI's API.
- 📊 **Interactive UI**: Streamlit interface displays results in a table with a CSV download option.

## 🧠 Workflow

1. **User Input**: Enter a prompt in the Streamlit UI (e.g., "plumbers near downtown LA").
2. **Prompt Correction**: Prompt is enhanced using Mistral (via Together.ai API) to suit Google Maps-style search.
3. **Search Results**: SearchAPI fetches a defined number of location-based results.
4. **Email Extraction**: If a result includes a website, the system scrapes the site to find contact emails using OpenAI's API.
5. **Result Display**: A detailed table is shown with all relevant info and a **Download CSV** button.

## 🗂️ Files

- **app.py**: Main app logic.
- **requirements.txt**: Dependencies.
- **.gitignore**: Ignores .env and other unwanted files.
- **.env**: (not uploaded) stores API keys.

## 🏃 To run this file type the command below in the terminal
- streamlit run app.py
