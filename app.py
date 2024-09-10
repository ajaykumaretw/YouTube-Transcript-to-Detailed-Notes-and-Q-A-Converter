import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from deep_translator import GoogleTranslator, single_detection
import time

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

# Improved function to translate Hindi transcript to English using deep_translator
def translate_if_hindi(text):
    if not text:
        st.error("No text available for translation.")
        return ""

    max_retries = 3  # Maximum retries for translation
    
    for attempt in range(max_retries):
        try:
            # Detect the language
            detected_lang = single_detection(text[:100], api_key=os.getenv("GOOGLE_API_KEY"))
            
            if detected_lang == 'hi':
                st.info("Detected Hindi transcript. Translating to English...")
                translator = GoogleTranslator(source='hi', target='en')
                # Split the text into smaller chunks to avoid length limits
                chunk_size = 5000  # Adjust this value based on the library's limitations
                chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
                translated_chunks = [translator.translate(chunk) for chunk in chunks]
                return ' '.join(translated_chunks)
            return text
        except Exception as e:
            st.error(f"Translation Error (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait for 2 seconds before retrying
            else:
                st.warning("Max retries reached. Returning original text.")
                return text
    
    return text

# Improved function to get transcript details from YouTube videos
def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("v=")[-1]
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to get the English transcript, if not available, get Hindi
        try:
            transcript = transcripts.find_manually_created_transcript(['en'])
            if transcript:
                transcript_data = transcript.fetch()
            else:
                raise NoTranscriptFound("No English transcript found.")
        except NoTranscriptFound:
            try:
                transcript = transcripts.find_generated_transcript(['hi'])
                if transcript:
                    transcript_data = transcript.fetch()
                    st.info("Hindi transcript found; translating to English...")
                else:
                    raise NoTranscriptFound("No Hindi transcript found.")
            except NoTranscriptFound:
                st.error("No suitable transcript found for this video.")
                return None

        # Check if the fetched transcript is correctly formatted
        if isinstance(transcript_data, list) and all(isinstance(entry, dict) for entry in transcript_data):
            transcript_text = " ".join([entry.get("text", "") for entry in transcript_data if entry.get("text")])
            if transcript.language_code == 'hi':
                transcript_text = translate_if_hindi(transcript_text)
            return transcript_text
        else:
            st.error("Transcript format is not as expected.")
            return None

    except TranscriptsDisabled:
        st.error("Transcripts are disabled for this video.")
        return None
    except Exception as e:
        st.error(f"Error fetching transcript: {e}")
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