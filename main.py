import os
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from pydantic import BaseModel, Field
import streamlit as st
import requests

# Load environment variables from a .env file
_ = load_dotenv(find_dotenv())


# Initialize OpenAI client with API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# get apify key from env variables
APIFY_TOKEN = os.getenv("APIFY_API_KEY")


class ProductInfo(BaseModel):
    company_name: str = Field(..., description="Name of the company")
    description: str = Field(..., description="Description of the company")
    industry: str = Field(..., description="Industry sector of the company")
    size: str = Field(..., description="Size of the company")
    public_private: str = Field(...,
                                description="Whether the company is public or private")
    hq: str = Field(..., description="Headquarters location of the company")
    score: float = Field(..., description="Relevance score")
    website: str = Field(..., description="Company website URL")


def main():
    response = None
    instagram_response = None
    facebook_response = None
    st.set_page_config(
        page_title="Company Information Extractor", page_icon=":mag_right:")

    st.sidebar.title("Company Information Extractor")
    st.sidebar.write(
        "Enter a company name or keyword to get structured information.")

    input_text = st.sidebar.text_input("Company Name or Keyword")
    tab1, tab2, tab3 = st.tabs(
        [f"{input_text.capitalize()} Info", "Instagram", "Facebook"])

    if st.sidebar.button("Get Information"):
        response = client.responses.parse(
            model="gpt-4o",
            tools=[
                {"type": "web_search"}
            ],
            input=f"""
            Tell me about {input_text} and provide output
            company name,
            description need at least 8 lines,
            Industry, Size, Public/Private, Headquarters, score, and website in json format.
            """,
            text_format=ProductInfo,
            temperature=0.8
        )
        instagram_response = get_instagram(input_text)
        facebook_response = get_facebook(input_text.capitalize())

    with tab1:
        if response is not None:
            st.title("Extracted Company Information")
            st.json(response.output_parsed)
        else:
            st.write(
                "No data to display. Please enter a company name and click the button.")
    with tab2:
        if instagram_response is not None:
            st.title("Instagram Profile Information")
            st.json(instagram_response)
        else:
            st.write(
                "No data to display. Please enter a company name and click the button.")
    with tab3:
        if facebook_response is not None:
            st.title("Facebook Page Information")
            st.json(facebook_response)
        else:
            st.write(
                "No data to display. Please enter a company name and click the button.")


def get_instagram(username: str):
    ACTOR = "apify~instagram-profile-scraper"
    url = f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items?token={APIFY_TOKEN}"
    resp = requests.post(url, json={"usernames": [username]})
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return {}
    profile = data[0]
    # only select necessary fields
    profile = {
        "username": profile.get("username"),
        "name": profile.get("fullName"),
        "bio": profile.get("biography"),
        "followers": profile.get("followersCount"),
        "following": profile.get("followsCount"),
        "posts": profile.get("postsCount"),
        "profile_pic_url": profile.get("profilePicUrl"),
        "external_url": profile.get("externalUrl"),
    }
    return profile


def get_facebook(page_url: str):
    ACTOR = "apify~facebook-pages-scraper"
    url = f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items?token={APIFY_TOKEN}"
    resp = requests.post(
        url, json={"startUrls": [{"url": f"https://www.facebook.com/{page_url}", "method": "GET"}]})
    resp.raise_for_status()
    data = resp.json()
    # only select necessary fields
    # return data[0] if data else {}
    if not data:
        return {}
    profile = data[0]
    # only select necessary fields
    profile = {
        "username": profile.get("title"),
        "intro": profile.get("intro"),
        "followers": profile.get("followers"),
        "ratings": profile.get("ratings"),
        "likes": profile.get("likes"),
        "profile_pic_url": profile.get("profilePictureUrl"),
        "website_url": profile.get("website"),
    }
    return profile


if __name__ == "__main__":
    main()
