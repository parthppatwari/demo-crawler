import streamlit as st
import requests
from urllib.parse import urljoin
import openai
from dotenv import load_dotenv
import os

load_dotenv()

# === CONFIG ===
client = openai.OpenAI(api_key=os.getenv("OPENAI_API"))  # Replace with your key
TOGETHER_API_KEY = os.getenv("TOGETHER_API")
SEARCHAPI_KEY = os.getenv("SEARCH_API")
TOGETHER_MODEL = "mistralai/Mistral-7B-Instruct-v0.1"

# === TOGETHER.AI: Prompt → Clean Query ===
def extract_search_query(user_prompt):
    system_prompt = (
        "You are an assistant that extracts clean Google Maps search strings from user input.\n"
        "Respond only with the query to search in Google Maps."
    )

    body = {
        "model": TOGETHER_MODEL,
        "max_tokens": 50,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    res = requests.post(
        "https://api.together.xyz/v1/chat/completions",
        headers={"Authorization": f"Bearer {TOGETHER_API_KEY}"},
        json=body
    )

    return res.json()["choices"][0]["message"]["content"].strip()

# === SEARCHAPI.IO ===
def search_maps(query):
    url = "https://www.searchapi.io/api/v1/search"
    params = {
        "engine": "google_maps",
        "q": query,
        "hl": "en",
        "api_key": SEARCHAPI_KEY
    }
    res = requests.get(url, params=params)
    return res.json().get("local_results", [])

# === EMAIL SCRAPER ===
def find_email_on_page(url):
    try:
        response = client.responses.create(
            model="gpt-4.1",
            temperature=0,
            tools=[{"type": "web_search_preview"}],
            input=f"get the first email from this website without censoring it:{url} and nothing else. if no email id is found then return 'nothing here'"
        )
        return response.output_text
    except Exception as e:
        st.warning("⚠️ GPT error: " + str(e))
        return None

# === GET EMAIL FROM WEBSITE AND FALLBACK PAGES ===
def get_best_email(website_url):
    paths = ["", "/contact", "/about", "/contact-us", "/about-us"]
    for path in paths:
        full_url = urljoin(website_url, path)
        email = find_email_on_page(full_url)
        if email and "nothing here" not in email.lower():
            return email
    return "Not found"

# === STREAMLIT UI ===
st.set_page_config(page_title="Google Maps Email Scraper", layout="wide")
st.title("🗺️ Google Maps Email Scraper")

prompt = st.text_input("Enter your search query (e.g., 'best dermatologists in Mumbai')")

if st.button("Search"):
    if not prompt.strip():
        st.warning("Please enter a search query.")
    else:
        with st.spinner("🔍 Extracting clean search from prompt..."):
            query = extract_search_query(prompt)
        
        with st.spinner(f"🔍 Searching Google Maps for: `{query}`"):
            listings = search_maps(query)

        if not listings:
            st.error("No listings found or SearchAPI returned nothing.")
        else:
            st.success(f"✅ Found {len(listings)} results. Fetching emails...")

            results = []
            for i, item in enumerate(listings):
                website = item.get("website", "")
                email = item.get("email", "")
                if not email and website:
                    with st.spinner(f"[{i+1}/{len(listings)}] Getting email from {website}"):
                        email = get_best_email(website)

                results.append({
                    "Name": item.get("title", ""),
                    "Phone": item.get("phone", ""),
                    "Address": item.get("address", ""),
                    "Website": website,
                    "Email": email,
                    "Rating": item.get("rating", ""),
                    "Reviews": item.get("reviews", "")
                })

            st.dataframe(results, use_container_width=True)
