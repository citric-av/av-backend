from pytube import YouTube
import os
from dotenv import load_dotenv
from pydub import AudioSegment
from openai import OpenAI
import whisper
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def filter_sentences_with_context(transcript_timestamped, keywords):
    keywords_list = keywords.split(', ')
    filtered_sentences = []
    chunk = []
    chunk_start_time = None
    chunk_end_time = None
    
    for i, sentence in enumerate(transcript_timestamped):
        contains_keyword = any(keyword.lower() in sentence['text'].lower() for keyword in keywords_list)

        if contains_keyword:
            if not chunk:
                chunk_start_time = transcript_timestamped[i-1]['start'] if i > 0 else sentence['start']
                if i > 0:
                    chunk.append(transcript_timestamped[i-1]['text'])
            chunk.append(sentence['text'])
            chunk_end_time = sentence['end']

        elif chunk:
            chunk.append(sentence['text'])
            chunk_end_time = sentence['end']
            chunk_text = '... ' + ' '.join(chunk) + ' ...'
            filtered_sentences.append({"text": chunk_text, "start": chunk_start_time, "end": chunk_end_time})
            chunk = []
            chunk_start_time = None
            chunk_end_time = None

    if chunk:
        chunk_text = '... ' + ' '.join(chunk) + ' ...'
        chunk_end_time = chunk_end_time if chunk_end_time else transcript_timestamped[-1]['end']
        filtered_sentences.append({"text": chunk_text, "start": chunk_start_time, "end": chunk_end_time})

    return filtered_sentences

# YouTube Download Module
def download_yt_audio(youtube_url):
    yt = YouTube(youtube_url)
    audio_stream = yt.streams.filter(only_audio=True).first()
    audio_filename = audio_stream.default_filename
    audio_stream.download(filename=audio_filename)
    return audio_filename

# Audio Conversion Module
def convert_audio(audio_filename):
    audio = AudioSegment.from_file(audio_filename, format="mp4")
    converted_audio_filename = audio_filename + "_converted.wav"
    audio.set_channels(1).set_frame_rate(16000).export(converted_audio_filename, format="wav")
    return converted_audio_filename

# Transcription Module
def transcribe_audio(converted_audio_filename, keywords):
    model = whisper.load_model("small")  # Choose the model size
    result = model.transcribe(converted_audio_filename)
    transcript = result["text"]
    transcript_sentences = result["segments"] # Transcript with all available parameters per sentence
    transcript_timestamped = [{'start': int(entry['start']), 'end': int(entry['end']), 'text': entry['text'].strip()} for entry in transcript_sentences]
    transcript_filtered = filter_sentences_with_context(transcript_timestamped, keywords)
    return transcript, transcript_timestamped, transcript_filtered

# Sentiment Analysis Module
def analyze_sentiments(filtered_sentences):
    analyzer = SentimentIntensityAnalyzer()
    sentiment_results = []
    for sentence in filtered_sentences:
        sentiment = analyzer.polarity_scores(sentence['text'])
        sentiment_results.append({'text': sentence['text'], 'sentiment': sentiment})
    return sentiment_results

# Summarization Module
def summariza_batonga(text, length, keywords, kw_analysis_length):
    load_dotenv()
    openai_api_key = os.getenv('OPENAI_API_KEY')
    client = OpenAI(api_key = openai_api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": "You are a helpful video transcriber tool."},
            {"role": "user", "content": f"Summarize the following video transcript in a strict length of {length} sentences: {text}. In the summary, avoid specifying the speaker's identity and use gender-neutral pronouns like 'they' or 'them'. After the summary, analyze how the following keywords are discussed in the video: {keywords}. Provide a separate analysis for each keyword, limited to {kw_analysis_length} sentences per keyword. Ensure there is a break between the analysis of different keywords."}
        ]
    )
    return response.choices[0].message.content