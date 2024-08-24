import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

# Load environment variables
load_dotenv()

# Configure Google Generative AI with API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Define prompts for summarization and Q&A
prompt_summary = """You are a YouTube video summarizer. You will be taking the transcript text
and summarizing the entire video, providing the important summary in points
within 250 words. Please provide the summary of the text given here:  """

prompt_qa = """You are a Q&A assistant. Based on the provided transcript text, answer the following question in detail. 
The transcript text is: {} 
The question is: {}"""

# Function to get transcript details from YouTube videos
def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("v=")[-1]
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)

        transcript = " ".join([entry["text"] for entry in transcript_text])
        return transcript

    except Exception as e:
        st.error(f"Error extracting transcript: {e}")
        return None

# Function to generate summary or answer based on prompt from Google Gemini
def generate_gemini_content(prompt, transcript_text, question=None):
    try:
        model = genai.GenerativeModel("gemini-pro")
        if question:
            full_prompt = prompt.format(transcript_text, question)
        else:
            full_prompt = prompt + transcript_text
        response = model.generate_content(full_prompt)
        return response.text

    except Exception as e:
        st.error(f"Error generating content: {e}")
        return None

# Streamlit app
st.title("YouTube Transcript to Detailed Notes and Q&A Converter")
youtube_link = st.text_input("Enter YouTube Video Link:")

if youtube_link:
    try:
        video_id = youtube_link.split("v=")[-1]
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)
    except Exception as e:
        st.error(f"Error displaying video thumbnail: {e}")

if st.button("Get Detailed Notes"):
    if youtube_link:
        transcript_text = extract_transcript_details(youtube_link)
        if transcript_text:
            summary = generate_gemini_content(prompt_summary, transcript_text)
            if summary:
                st.session_state.summary = summary

if "summary" in st.session_state:
    st.markdown("## Detailed Notes:")
    st.write(st.session_state.summary)

st.subheader("Ask a Question about the Video:")
question = st.text_input("Enter your question:")

if st.button("Get Answer"):
    if youtube_link and question:
        transcript_text = extract_transcript_details(youtube_link)
        if transcript_text:
            answer = generate_gemini_content(prompt_qa, transcript_text, question)
            if answer:
                st.session_state.answer = answer

if "answer" in st.session_state:
    st.markdown("## Answer:")
    st.write(st.session_state.answer)
