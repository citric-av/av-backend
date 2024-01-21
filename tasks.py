from rq import get_current_job
import os
from modules import download_yt_audio, convert_audio, transcribe_audio, summariza_batonga, analyze_sentiments

def analyze_yt_video(youtube_url, length, keywords, kw_analysis_length):
    current_job = get_current_job()
    
    # Step 1: Download audio
    current_job.meta['status'] = 'Downloading audio...'
    current_job.save_meta()
    try:  
        audio_filename = download_yt_audio(youtube_url)
    except Exception as e:
        error_str = str(e).lower()
        if 'match' in error_str or 'unavailable' in error_str:
            error_message = "The provided video link is invalid. Please check the link and try again."
        else:
            error_message = f"An error occurred while downloading the video: {e}"
        current_job.meta['status'] = error_message
        current_job.save_meta()
        raise RuntimeError(error_message)

    # Step 2: Convert audio to WAV
    current_job.meta['status'] = 'Converting audio...'
    current_job.save_meta()
    try:
        converted_audio_filename = convert_audio(audio_filename)
    except Exception as e:
        error_message = f"An error occurred while converting the audio: {e}"
        current_job.meta['status'] = error_message
        current_job.save_meta()
        raise RuntimeError(error_message)

    # Step 3: Transcribe audio
    current_job.meta['status'] = 'Transcribing audio... This may take a while.'
    current_job.save_meta()
    try:
        transcript, transcript_timestamped, transcript_filtered = transcribe_audio(converted_audio_filename, keywords)
    except Exception as e:
        error_message = f"An error occurred while transcribing audio: {e}"
        current_job.meta['status'] = error_message
        current_job.save_meta()
        raise RuntimeError(error_message)

    # Step 4: Analyze sentiment
    try:
        sentiment_results = analyze_sentiments(transcript_filtered)
    except Exception as e:
        error_message = f"An error occurred while analyzing sentiment: {e}"
        current_job.meta['status'] = error_message
        current_job.save_meta()
        raise RuntimeError(error_message)

    # Step 5: Summarize transcript
    try:
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
        'transcript_timestamped': transcript_timestamped,
        'transcript_filtered': transcript_filtered,
        'sentiment_analysis': sentiment_results,
        'summary': summary
    }