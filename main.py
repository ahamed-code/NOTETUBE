import streamlit as st
import re
import os
import whisper
import yt_dlp
from transformers import pipeline
from docx import Document
from fpdf import FPDF

# Function to save content as a TXT file
def save_as_txt(content, file_name):
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(content)

# Function to save content as a Word file
def save_as_word(content, file_name):
    doc = Document()
    doc.add_paragraph(content)
    doc.save(file_name)

# Function to save content as a PDF file
def save_as_pdf(content, file_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, content)
    pdf.output(file_name)

# Function to extract video ID
def get_video_id(url):
    match = re.search(r"(?:v=|\/|youtu\.be\/|embed\/|shorts\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

# Function to download YouTube audio using yt-dlp
def download_audio(video_url):
    audio_path = "audio.mp4"  # Save as MP4

    try:
        st.info("🔄 Attempting to download audio from YouTube...")
        ydl_opts = {
            'format': 'bestaudio/best',  # Best audio quality
            'outtmpl': audio_path,       # Save location for audio
            'quiet': True                # Avoid verbose output
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

# Function to transcribe audio using Whisper AI
def transcribe_audio(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    st.info("📝 Transcribing audio to text...")
    model = whisper.load_model("base")
    result = model.transcribe(file_path)
    return result["text"]

# Function to classify transcript into notes with subtopics and paragraphs
def classify_notes(transcript):
    try:
        # Truncate the transcript if it's too long
        max_input_length = 1024  # Adjust based on the model's max input size
        truncated_transcript = transcript[:max_input_length]

        # Use a summarization pipeline from Hugging Face
        st.info("📝 Organizing notes using Hugging Face model...")
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=-1)  # Use CPU
        summary = summarizer(truncated_transcript, max_length=200, min_length=50, do_sample=False)
        return summary[0]["summary_text"]
    except Exception as e:
        return f"⚠️ Error generating notes: {str(e)}"

# Streamlit UI
st.set_page_config(page_title="YouTube Video Transcriber", layout="centered")
st.title("🎙️NOTETUBE")
st.write("Convert any YouTube video audio into text and organize it into structured notes.")
st.write("symbol of productivity")
# Initialize session state for storing data
if "transcript_text" not in st.session_state:
    st.session_state.transcript_text = None
if "notes" not in st.session_state:
    st.session_state.notes = None

# Input for YouTube URL
video_url = st.text_input("Enter YouTube Video URL", placeholder="Paste YouTube link here...")

# Transcribe button
if st.button("Transcribe & Organize Notes"):
    video_id = get_video_id(video_url)

    if not video_id:
        st.error("⚠️ Invalid YouTube URL. Please check the link.")
    else:
        st.info("🎵 Downloading audio from video...")
        audio_path = download_audio(video_url)

        if audio_path:
            st.success("✅ Audio downloaded! Transcribing...")
            try:
                transcript_text = transcribe_audio(audio_path)

                if transcript_text:
                    st.session_state.transcript_text = transcript_text  # Save transcript in session state
                    st.success("✅ Transcription complete! Organizing notes...")
                    notes = classify_notes(transcript_text)
                    st.session_state.notes = notes  # Save notes in session state

                else:
                    st.error("❌ Failed to transcribe the audio.")
            except FileNotFoundError as e:
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

    # Dropdown for download format
    download_format = st.selectbox("Choose download format:", ["TXT", "Word", "PDF"])

    # Save and download Notes
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