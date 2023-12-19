from pytube import YouTube
from rq import get_current_job
import os
from pydub import AudioSegment
import numpy as np
import wave
import requests
from openai import OpenAI
import whisper

client = OpenAI(
    api_key = ""
)

def summarize(text):
    inputs = tokenizer(text, max_length=1024, return_tensors='pt', truncation=True)
    summary_ids = model.generate(inputs.input_ids)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

def summariza_batonga(text):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Summarize a video according to this transcript: {text}"}
        ]
    )
    return response.choices[0].message.content

def load_wav_file(filename):
    with wave.open(filename, 'rb') as w:
        rate = w.getframerate()
        frames = w.getnframes()
        buffer = w.readframes(frames)
    return buffer, rate

def transcribe(youtube_url):
    current_job = get_current_job()

    # Step 1: Download audio
    current_job.meta['status'] = 'downloading audio'
    current_job.save_meta()
    yt = YouTube(youtube_url)
    audio_stream = yt.streams.filter(only_audio=True).first()
    audio_filename = audio_stream.default_filename
    audio_stream.download(filename=audio_filename)

    # Convert the audio to the desired format
    audio = AudioSegment.from_file(audio_filename, format="mp4")
    converted_audio_filename = "converted_audio.wav"
    audio.set_channels(1).set_frame_rate(16000).export(converted_audio_filename, format="wav")

    # Load the WAV file
    audio_data, rate = load_wav_file(converted_audio_filename)
    audio_np = np.frombuffer(audio_data, dtype=np.int16)

    # Step 2: Transcribe using Whisper
    current_job.meta['status'] = 'transcribing audio'
    current_job.save_meta()
    model = whisper.load_model("small")  # Choose the model size
    result = model.transcribe(converted_audio_filename)
    transcript = result["text"]
    
    # Step 3: Summarize transcript
    current_job.meta['status'] = 'summarizing transcript'
    current_job.save_meta()
    summary = summariza_batonga(transcript)

    # Cleanup
    os.remove(audio_filename)
    os.remove(converted_audio_filename)

    return {
        'transcript': transcript,  # This is the original transcript
        'summary': summary              # This is the summarized text
    }
