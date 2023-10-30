from pytube import YouTube
import deepspeech
from rq import get_current_job
import os
# from punctuator import Punctuator
from pydub import AudioSegment
import numpy as np
import wave
import requests

# Load DeepSpeech model
ds_model_path = 'assets/deepspeech-0.9.3-models.pbmm'
ds_scorer_path = 'assets/deepspeech-0.9.3-models.scorer'
ds_model = deepspeech.Model(ds_model_path)
ds_model.enableExternalScorer(ds_scorer_path)

# Load Punctuator model
# punctuator_model = Punctuator('assets/punctuator-demo.pcl')

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

    # Step 2: Transcribe with DeepSpeech
    current_job.meta['status'] = 'transcribing audio'
    current_job.save_meta()
    transcript = ds_model.stt(audio_np)

    # Step 3: Punctuate the transcript using the remote service
    current_job.meta['status'] = 'punctuating transcript'
    current_job.save_meta()

    # Make the HTTP POST request
    response = requests.post(
        "http://bark.phon.ioc.ee/punctuator",
        data={'text': transcript}
    )

    # Check if the request was successful
    if response.status_code == 200:
        punctuated_text = response.text
    else:
        # Handle the error as appropriate for your application
        raise Exception("Failed to get punctuated text from remote service.")


    # Cleanup
    os.remove(audio_filename)
    os.remove(converted_audio_filename)

    return punctuated_text
