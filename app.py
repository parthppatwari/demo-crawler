# app prototype #2
import streamlit as st
import requests
from urllib.parse import urljoin
import openai
from dotenv import load_dotenv
import os

# Load .env if running locally
load_dotenv()

# === CONFIG ===
OPENAI_API_KEY = st.secrets.get("OPENAI_API", os.getenv("OPENAI_API"))
TOGETHER_API_KEY = st.secrets.get("TOGETHER_API", os.getenv("TOGETHER_API"))
SEARCHAPI_KEY = st.secrets.get("SEARCH_API", os.getenv("SEARCH_API"))

TOGETHER_MODEL = "mistralai/Mistral-7B-Instruct-v0.1"
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# === CLEAN QUERY FROM TOGETHER.AI ===
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

# === SEARCHAPI.IO PAGINATED SEARCH ===
def search_maps(query, max_results):
    url = "https://www.searchapi.io/api/v1/search"
    listings = []

    for offset in range(0, max_results, 20):
        params = {
            "engine": "google_maps",
            "q": query,
            "hl": "en",
            "start": offset,
            "api_key": SEARCHAPI_KEY
        }

        try:
            res = requests.get(url, params=params)
            data = res.json()

            local_results = data.get("local_results", [])
            if not local_results:
                break  # Stop if there are no more results

            listings.extend(local_results)

            if len(local_results) < 20:
                break  # No more pages left even if user requested more
        except Exception as e:
            st.error(f"SearchAPI Error at offset {offset}: {e}")
            break

    return listings


# === GPT-POWERED EMAIL SCRAPER ===
def find_email_on_page(url):
    try:
        response = client.responses.create(
            model="gpt-4.1",
            temperature=0,
            tools=[{"type": "web_search_preview"}],
            input=f"get the first email from this website without censoring it:{url} and nothing else. if no email id is found then return 'nothing here'"
        )
        return response.output_text.strip()
    except Exception as e:
        st.warning("⚠️ GPT Error: " + str(e))
        return "error"

# === CHECK COMMON PATHS FOR EMAIL ===
def get_best_email(website_url):
    paths = ["", "/contact", "/about", "/contact-us", "/about-us"]
    for path in paths:
        full_url = urljoin(website_url, path)
        email = find_email_on_page(full_url)
        if email and "nothing here" not in email.lower():
            return email
    return "Not found"

# === CSV CONVERTER ===
def convert_to_csv(data):
    import pandas as pd
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode("utf-8")


# === STREAMLIT APP ===
st.set_page_config(page_title="Google Maps Email Scraper", layout="wide")
st.title("🗺️ Google Maps Email Scraper")

with st.form("search_form"):
    prompt = st.text_input("Enter your search query", placeholder="e.g., best pediatricians in Pune")
    num_results = st.number_input(
        "How many results to fetch?",
        value=20,
        step=1,
        format = "%d"
    )

    submitted = st.form_submit_button("Search")

if submitted:
    if not prompt.strip():
        st.warning("Please enter a valid prompt.")
    else:
        with st.spinner("🧠 Extracting clean query..."):
            query = extract_search_query(prompt)

        with st.spinner(f"🔍 Searching Google Maps for: `{query}`"):
            listings = search_maps(query, max_results=num_results)

        if not listings:
            st.error("No results found.")
        else:
            st.success(f"✅ Found {len(listings)} listings. Scraping emails...")

            results = []
            progress_bar = st.progress(0)
            status_box = st.empty()

            results = []

            for i, item in enumerate(listings):
                name = item.get("title", "")
                website = item.get("website", "")
                email = item.get("email", "")

                # Show progress %
                progress = (i + 1) / len(listings)
                progress_bar.progress(progress)

                # Temporary status message
                status_box.info(f"📧 Scraping email from: {name}")

                if not email and website:
                    email = get_best_email(website)

                results.append({
                    "Name": name,
                    "Phone": item.get("phone", ""),
                    "Address": item.get("address", ""),
                    "Website": website,
                    "Email": email,
                    "Rating": item.get("rating", ""),
                    "Reviews": item.get("reviews", "")
                })

                # Cleanup progress UI
                progress_bar.empty()
                status_box.success("✅ All emails scraped.")



            st.dataframe(results, use_container_width=True)

            # Optionally download as CSV
            st.download_button("⬇️ Download Results as CSV", data=convert_to_csv(results),
                               file_name="scraped_results.csv", mime="text/csv")
