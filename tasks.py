from pytube import YouTube
from rq import get_current_job
import os
from dotenv import load_dotenv
from pydub import AudioSegment
import numpy as np
import wave
import requests
from openai import OpenAI
import whisper

load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI(
    api_key = openai_api_key
)

def summarize(text):
    inputs = tokenizer(text, max_length=1024, return_tensors='pt', truncation=True)
    summary_ids = model.generate(inputs.input_ids)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

def summariza_batonga(text, length, keywords, kw_analysis_length):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful video transcriber tool."},
            {"role": "user", "content": f"Summarize the following video transcript in a strict length of {length} sentences: {text}. In the summary, avoid specifying the speaker's identity and use gender-neutral pronouns like 'they' or 'them'. After the summary, analyze how the following keywords are discussed in the video: {keywords}. Provide a separate analysis for each keyword, limited to {kw_analysis_length} sentences per keyword. Ensure there is a break between the analysis of different keywords."}
        ]
    )
    return response.choices[0].message.content

def filter_sentences_with_context(transcript, keywords):
    keywords_list = keywords.split(', ')
    filtered_sentences = []
    chunk = []
    chunk_start_time = None
    chunk_end_time = None

    for i, sentence in enumerate(transcript):
        contains_keyword = any(keyword.lower() in sentence['text'].lower() for keyword in keywords_list)

        if contains_keyword:
            if not chunk:
                # Start a new chunk
                chunk_start_time = transcript[i-1]['start'] if i > 0 else sentence['start']
                if i > 0:
                    chunk.append(transcript[i-1]['text'])

            chunk.append(sentence['text'])

            # Update chunk end time
            chunk_end_time = sentence['end']

        elif chunk:
            # Add the next sentence and end the chunk
            chunk.append(sentence['text'])
            chunk_end_time = sentence['end']

            # Combine chunk into text and add ellipses
            chunk_text = '... ' + ' '.join(chunk) + ' ...'
            filtered_sentences.append({"text": chunk_text, "start": chunk_start_time, "end": chunk_end_time})

            # Reset for the next chunk
            chunk = []
            chunk_start_time = None
            chunk_end_time = None

    # Handle case where transcript ends with a keyword sentence
    if chunk:
        chunk_text = '... ' + ' '.join(chunk) + ' ...'
        chunk_end_time = chunk_end_time if chunk_end_time else transcript[-1]['end']
        filtered_sentences.append({"text": chunk_text, "start": chunk_start_time, "end": chunk_end_time})

    return filtered_sentences

def load_wav_file(filename):
    with wave.open(filename, 'rb') as w:
        rate = w.getframerate()
        frames = w.getnframes()
        buffer = w.readframes(frames)
    return buffer, rate

def transcribe(youtube_url, length, keywords, kw_analysis_length):
    current_job = get_current_job()

    try:
        # Step 1: Download audio
        current_job.meta['status'] = 'Downloading audio...'
        current_job.save_meta()
        yt = YouTube(youtube_url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        audio_filename = audio_stream.default_filename
        audio_stream.download(filename=audio_filename)
    except Exception as e:
        if 'match' in str(e).lower():
            error_message = "The provided video link is invalid. Please check the link and try again."
        else:
            error_message = f"An error occurred while downloading the video: {e}"
        current_job.meta['status'] = error_message
        current_job.save_meta()
        raise RuntimeError(error_message)

    try:
        # Convert the audio to the desired format
        audio = AudioSegment.from_file(audio_filename, format="mp4")
        converted_audio_filename = "converted_audio.wav"
        audio.set_channels(1).set_frame_rate(16000).export(converted_audio_filename, format="wav")

        # Load the WAV file
        # Assume load_wav_file is a defined function
        audio_data, rate = load_wav_file(converted_audio_filename)
        audio_np = np.frombuffer(audio_data, dtype=np.int16)

        # Step 2: Transcribe using Whisper
        current_job.meta['status'] = 'Transcribing audio... This may take a while.'
        current_job.save_meta()
        model = whisper.load_model("small")  # Choose the model size
        result = model.transcribe(converted_audio_filename)
        transcript = result["text"]
        transcript_sentences = result["segments"]
        transcript_timestamped = [{'start': int(entry['start']), 'end': int(entry['end']), 'text': entry['text'].strip()} for entry in transcript_sentences]
        transcript_filtered = filter_sentences_with_context(transcript_timestamped, keywords)
    except Exception as e:
        error_message = f"An error occurred while transcribing audio: {e}"
        current_job.meta['status'] = error_message
        current_job.save_meta()
        raise RuntimeError(error_message)

    try:
        # Step 3: Summarize transcript
        current_job.meta['status'] = 'Summarizing transcript...'
        current_job.save_meta()
        summary = summariza_batonga(transcript, length, keywords, kw_analysis_length)
    except Exception as e:
        if 'token' in str(e).lower():
            error_message = "An error occurred while summarizing the video: Maximum word count exceeded. Support for unlimited video length is coming in the next update, but in the meantime please try analyzing a shorter video. Sorry for the inconvenience."
        else:
            error_message = f"An error occurred while summarizing the transcript: {e}"
        current_job.meta['status'] = error_message
        current_job.save_meta()
        raise RuntimeError(error_message)

    # Cleanup
    os.remove(audio_filename)
    os.remove(converted_audio_filename)

    current_job.meta['status'] = 'task completed'
    current_job.save_meta()

    return {
        'transcript': transcript,
        'transcript_timestamped': transcript_timestamped,
        'transcript_filtered': transcript_filtered,
        'summary': summary
    }