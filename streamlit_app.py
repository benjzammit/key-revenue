import streamlit as st
import requests
import pandas as pd
import json
import google.generativeai as genai
from PIL import Image
from io import BytesIO
import re

# API configuration
INSTAGRAM_API_URL = "https://instagram-scraper-api3.p.rapidapi.com/user_reels"
INSTAGRAM_API_KEY = "d8d971f9bemsh5c96243d1184e59p11bed8jsn4960cb93f170"
INSTAGRAM_API_HOST = "instagram-scraper-api3.p.rapidapi.com"

# Load Google API Key from Streamlit Secrets
GOOGLE_API_KEY = st.secrets["api_keys"]["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)

def fetch_instagram_data(username):
    querystring = {"username_or_id": username}
    headers = {
        "x-rapidapi-key": INSTAGRAM_API_KEY,
        "x-rapidapi-host": INSTAGRAM_API_HOST
    }
    response = requests.get(INSTAGRAM_API_URL, headers=headers, params=querystring)
    return response.json()

def clean_and_parse_response(response_text):
    try:
        # Extract JSON content from the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
            return json.loads(json_text)
        else:
            print("No JSON content found in the response.")
            print(f"Response: {response_text}")
            return None
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Problematic JSON: {json_text}")
        return None

def analyze_reel_with_gemini(reel):
    caption = reel['media']['caption']['text'] if reel['media']['caption'] else ""
    views = reel['media']['play_count']
    likes = reel['media']['like_count']
    comments = reel['media']['comment_count']
    thumbnail_url = reel['media']['image_versions2']['candidates'][0]['url']
    video_url = reel['media']['video_versions'][0]['url']

    prompt = f"""
    Analyze the following Instagram Reel caption and identify the main topic:

    Caption: "{caption}"

    Please provide the analysis in strict JSON format with the following structure:

    {{
        "main_topic": "concise topic that categorizes the content of the reel",
        "subtopics": ["subtopic1", "subtopic2"],
        "sentiment": "positive" / "negative" / "neutral",
        "suggested_hashtags": ["#hashtag1", "#hashtag2"],
        "content_quality_score": integer between 0 and 10,
        "audience_engagement_score": integer between 0 and 10,
        "roi_potential_score": integer between 0 and 10,
        "summary": "brief summary of the content"
    }}

    **Output only the JSON data without any comments or additional text.**
    """

    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        response = model.generate_content(prompt)
        response_text = response.text
        analysis = clean_and_parse_response(response_text)
        if analysis is None:
            st.write(f"Failed to parse the following response from Gemini:\n{response_text}")
            analysis = {
                "main_topic": "Unknown",
                "subtopics": [],
                "sentiment": "N/A",
                "suggested_hashtags": ["#N/A"],
                "content_quality_score": 0,
                "audience_engagement_score": 0,
                "roi_potential_score": 0,
                "summary": "Unable to analyze"
            }
    except Exception as e:
        st.error(f"An error occurred during AI analysis: {e}")
        analysis = {
            "main_topic": "Unknown",
            "subtopics": [],
            "sentiment": "N/A",
            "suggested_hashtags": ["#N/A"],
            "content_quality_score": 0,
            "audience_engagement_score": 0,
            "roi_potential_score": 0,
            "summary": "Unable to analyze"
        }

    estimated_earnings = views * 0.01  # Assume 1 cent per view

    return {
        'analysis': analysis,
        'views': views,
        'likes': likes,
        'comments': comments,
        'estimated_earnings': estimated_earnings,
        'thumbnail_url': thumbnail_url,
        'video_url': video_url,
        'caption': caption
    }

def main():
    st.set_page_config(layout="wide")
    st.title("Instagram Reels Topic Analysis with Gemini AI")

    username = st.text_input("Enter Instagram username:")

    if st.button("Analyze"):
        with st.spinner("Fetching and analyzing data..."):
            try:
                data = fetch_instagram_data(username)

                if 'data' in data and 'items' in data['data']:
                    reels = data['data']['items']
                    results = []
                    topic_views = {}

                    for reel in reels:
                        analysis_result = analyze_reel_with_gemini(reel)
                        if analysis_result:
                            results.append(analysis_result)
                            # Aggregate views by main topic
                            topic = analysis_result['analysis'].get('main_topic', 'Unknown')
                            topic_views[topic] = topic_views.get(topic, 0) + analysis_result['views']
                        else:
                            st.warning("Skipping a reel due to analysis error.")

                    if results:
                        st.subheader("Analysis Results")

                        # Display reels in a grid layout
                        cols_per_row = 3
                        rows = [results[i:i + cols_per_row] for i in range(0, len(results), cols_per_row)]

                        for row in rows:
                            cols = st.columns(cols_per_row)
                            for col, result in zip(cols, row):
                                with col:
                                    st.image(result['thumbnail_url'], use_column_width=True)
                                    st.markdown(f"**Caption:** {result['caption']}")
                                    st.markdown(f"**Views:** {result['views']}")
                                    st.markdown(f"**Main Topic:** {result['analysis'].get('main_topic', 'N/A')}")
                                    st.markdown(f"**Estimated Earnings (€):** {result['estimated_earnings']:.2f}")
                                    st.markdown("---")

                        # Display views by main topic
                        topic_views_df = pd.DataFrame(list(topic_views.items()), columns=['Main Topic', 'Total Views'])
                        topic_views_df = topic_views_df.sort_values(by='Total Views', ascending=False)

                        st.subheader("Views by Main Topic")
                        st.bar_chart(topic_views_df.set_index('Main Topic'))

                        # Display overall statistics
                        total_views = sum(r['views'] for r in results)
                        total_earnings = sum(r['estimated_earnings'] for r in results)

                        st.subheader("Overall Statistics")
                        st.write(f"**Total Views:** {total_views}")
                        st.write(f"**Total Estimated Earnings (€):** {total_earnings:.2f}")
                    else:
                        st.error("No reels were successfully analyzed.")
                else:
                    st.error("Failed to fetch data. Please check the username and try again.")
            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.write("Please try again or contact support if the problem persists.")

if __name__ == "__main__":
    main()