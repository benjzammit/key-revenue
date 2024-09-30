import streamlit as st
import requests
import pandas as pd
import json
import google.generativeai as genai

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

def analyze_reel_with_gemini(reel):
    caption = reel['media']['caption']['text']
    views = reel['media']['play_count']
    likes = reel['media']['like_count']
    comments = reel['media']['comment_count']
    
    prompt = f"""
    Analyze the following Instagram Reel caption and provide insights:

    Caption: {caption}

    Please provide the following information in a JSON format:
    1. Extract the top 3 most relevant keywords from the caption.
    2. Determine the overall sentiment of the caption (positive, negative, or neutral).
    3. Identify the main topic or theme of the caption.
    4. Suggest 2 hashtags that would be relevant for this content.

    Respond with a JSON object in the following structure:
    {{
        "keywords": ["keyword1", "keyword2", "keyword3"],
        "sentiment": "positive/negative/neutral",
        "main_topic": "brief description of the main topic",
        "suggested_hashtags": ["#hashtag1", "#hashtag2"]
    }}
    """

    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    analysis = json.loads(response.text)
    
    # Estimate earnings (this is a simplified calculation)
    estimated_earnings = views * 0.01  # Assume 1 cent per view
    
    return {
        'analysis': analysis,
        'views': views,
        'likes': likes,
        'comments': comments,
        'estimated_earnings': estimated_earnings
    }

def main():
    st.title("Instagram Reels ROI Analysis with Gemini AI")
    
    username = st.text_input("Enter Instagram username:")
    
    if st.button("Analyze"):
        with st.spinner("Fetching and analyzing data..."):
            data = fetch_instagram_data(username)
            
            if 'data' in data and 'items' in data['data']:
                reels = data['data']['items']
                results = []
                
                for reel in reels:
                    analysis = analyze_reel_with_gemini(reel)
                    results.append(analysis)
                
                # Display results
                st.subheader("Analysis Results")
                
                for i, result in enumerate(results, 1):
                    st.write(f"Reel {i}:")
                    st.write(f"Top Keywords: {', '.join(result['analysis']['keywords'])}")
                    st.write(f"Sentiment: {result['analysis']['sentiment']}")
                    st.write(f"Main Topic: {result['analysis']['main_topic']}")
                    st.write(f"Suggested Hashtags: {', '.join(result['analysis']['suggested_hashtags'])}")
                    st.write(f"Views: {result['views']}")
                    st.write(f"Likes: {result['likes']}")
                    st.write(f"Comments: {result['comments']}")
                    st.write(f"Estimated Earnings: €{result['estimated_earnings']:.2f}")
                    st.write("---")
                
                # Overall statistics
                total_views = sum(r['views'] for r in results)
                total_earnings = sum(r['estimated_earnings'] for r in results)
                
                st.subheader("Overall Statistics")
                st.write(f"Total Views: {total_views}")
                st.write(f"Total Estimated Earnings: €{total_earnings:.2f}")
                
            else:
                st.error("Failed to fetch data. Please check the username and try again.")

if __name__ == "__main__":
    main()