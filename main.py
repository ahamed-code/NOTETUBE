import streamlit as st
import re
import os
import yt_dlp
import requests
from transformers import pipeline
from docx import Document
from fpdf import FPDF
import time


ASSEMBLYAI_API_KEY = st.secrets["b0d66bcb26e3466c97c04529399cb963"]
HEADERS = {"authorization": ASSEMBLYAI_API_KEY}


def save_as_txt(content, file_name):
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(content)

def save_as_word(content, file_name):
    doc = Document()
    doc.add_paragraph(content)
    doc.save(file_name)

def save_as_pdf(content, file_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, content)
    pdf.output(file_name)

def get_video_id(url):
    match = re.search(r"(?:v=|\/|youtu\.be\/|embed\/|shorts\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

def download_audio(video_url):
    audio_path = "audio.mp3"
    try:
        st.info("🔄 Attempting to download audio from YouTube...")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': audio_path,
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        if os.path.exists(audio_path):
            st.success(f"✅ Audio successfully downloaded to: {audio_path}")
            return audio_path
        else:
            st.error("❌ Audio file was not created.")
            return None
    except Exception as e:
        st.error(f"❌ Error downloading audio: {str(e)}")
        return None


def upload_audio(file_path):
    """Upload audio file to AssemblyAI"""
    st.info("📤 Uploading audio to AssemblyAI...")
    with open(file_path, "rb") as f:
        response = requests.post("https://api.assemblyai.com/v2/upload", headers=HEADERS, data=f)
    audio_url = response.json()["upload_url"]
    st.success("✅ Upload complete!")
    return audio_url

def transcribe_and_summarize(audio_url):
    """Request AssemblyAI for transcription + summarization"""
    st.info("📝 Sending request to AssemblyAI for transcription & notes...")

    endpoint = "https://api.assemblyai.com/v2/transcript"
    json_data = {
        "audio_url": audio_url,
        "summarization": True,
        "summary_model": "informative",
        "summary_type": "bullets"  
    }
    response = requests.post(endpoint, json=json_data, headers=HEADERS)
    transcript_id = response.json()["id"]
 
    status = "queued"
    while status not in ["completed", "error"]:
        poll = requests.get(endpoint + "/" + transcript_id, headers=HEADERS).json()
        status = poll["status"]
        if status == "completed":
            return poll["text"], poll["summary"]
        elif status == "error":
            raise Exception(poll["error"])
        time.sleep(5)

 
st.set_page_config(page_title="YouTube Video Transcriber", layout="centered")
st.title("🎙️ NOTETUBE (AI Powered by AssemblyAI)")
st.write("Convert any YouTube video audio into text and organize it into structured notes.")
st.write("symbol of productivity")

# Initialize session state
if "transcript_text" not in st.session_state:
    st.session_state.transcript_text = None
if "notes" not in st.session_state:
    st.session_state.notes = None

 
video_url = st.text_input("Enter YouTube Video URL", placeholder="Paste YouTube link here...")

 
if st.button("Transcribe & Organize Notes"):
    video_id = get_video_id(video_url)
    if not video_id:
        st.error("⚠️ Invalid YouTube URL. Please check the link.")
    else:
        st.info("🎵 Downloading audio from video...")
        audio_path = download_audio(video_url)
        if audio_path:
            st.success("✅ Audio downloaded!")
            try:
                audio_url = upload_audio(audio_path)
                transcript_text, notes = transcribe_and_summarize(audio_url)

                st.session_state.transcript_text = transcript_text
                st.session_state.notes = "\n".join(notes) if isinstance(notes, list) else notes

                st.success("✅ Transcription & Notes generated successfully!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        else:
            st.error("❌ Failed to download audio.")

# Display Transcript and Notes if available
if st.session_state.transcript_text:
    st.subheader("📜 AI-Generated Transcript:")
    st.text_area("Full Transcript", st.session_state.transcript_text, height=300)

if st.session_state.notes:
    st.subheader("📝 Organized Notes:")
    st.text_area("Notes", st.session_state.notes, height=300)

     
    download_format = st.selectbox("Choose download format:", ["TXT", "Word", "PDF"])
 
    notes_file_name = f"organized_notes.{download_format.lower()}"
    if download_format == "TXT":
        save_as_txt(st.session_state.notes, notes_file_name)
    elif download_format == "Word":
        save_as_word(st.session_state.notes, notes_file_name)
    elif download_format == "PDF":
        save_as_pdf(st.session_state.notes, notes_file_name)

    with open(notes_file_name, "rb") as f:
        st.download_button(
            label=f"📥 Download Notes as {download_format}",
            data=f,
            file_name=notes_file_name,
            mime="application/octet-stream"
        )

    # Save and download Transcript
    transcript_file_name = f"transcript.{download_format.lower()}"
    if download_format == "TXT":
        save_as_txt(st.session_state.transcript_text, transcript_file_name)
    elif download_format == "Word":
        save_as_word(st.session_state.transcript_text, transcript_file_name)
    elif download_format == "PDF":
        save_as_pdf(st.session_state.transcript_text, transcript_file_name)

    with open(transcript_file_name, "rb") as f:
        st.download_button(
            label=f"📥 Download Transcript as {download_format}",
            data=f,
            file_name=transcript_file_name,
            mime="application/octet-stream"
        )
