try:
    import os
    from modules import download_yt_audio, convert_audio, transcribe_audio, summariza_batonga, analyze_sentiments
    from pytube import YouTube
    import time
    import speedtest
    import requests
    import argparse
    from dotenv import load_dotenv
except ImportError as e:
    print("\nError: You are currently running Python without required dependencies.\n\nPlease execute the setup script by running './initial_setup.sh' in your terminal.\nIf you already ran the setup script, you can switch to the appropriate virtual environment by running 'source venv/bin/activate'.\n")
    exit(1)

def main(args):
    yt_url = args.yt_url
    summary_length = args.summary_length
    keywords = args.keywords
    kw_analysis_length = args.kw_analysis_length

    os.system("clear")
    greeting()
    press_enter_to_continue()
    os.system("clear")

    print("\n🌐 Running network tests...\n")
    check_connection()
    check_endpoints()

    print("⚡ Checking internet speed...\n")
    download_speed, upload_speed, ping = connection_speedtest()

    try:
        yt = YouTube(yt_url)
        print("Youtube Video:", yt.title)
        print("Video Length:", format_duration(yt.length),"\n")
    except:
        print("Error: Invalid YouTube URL.\nPlease check the link and try again.\n")
        exit(1)

    print("📊 Starting benchmark...\n")
    benchmark(yt_url, summary_length, keywords, kw_analysis_length)

    

def greeting():
    welcome_message = "\n👋 Welcome to our performance benchmark!\n  "
    description = "This script will execute a real analysis run on your chosen YouTube video and record\nthe time taken for each module to complete.\n\nWhen the run is over, you will get estimated performance metrics for your system."
    print(welcome_message)
    print(description)

def press_enter_to_continue():
    input("\nPress Enter to continue...")

def check_connection():
    try:
        response = requests.get("https://8.8.8.8", timeout=5)
        print("Internet connection: ✅")
    except requests.RequestException:
        print("Internet connection: ❌")
        print("\nError: No internet connection detected.\nPlease connect to the internet and try again.\n")
        exit(1)

def check_endpoints():
    # YouTube
    try:
        response = requests.get("https://www.youtube.com", timeout=5)
        print("YouTube: ✅")
    except requests.RequestException:
        print("YouTube: ❌")
        print("\nError: YouTube is currently unavailable.\nPlease try again later.\n")
        exit(1)

    # OpenAI API
    model_name = "gpt-3.5-turbo-1106"
    try:
        url = "https://api.openai.com/v1/models/gpt-3.5-turbo-1106"
        load_dotenv()
        openai_api_key = os.getenv('OPENAI_API_KEY')
        headers = {
            "Authorization": f"Bearer {openai_api_key}"
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            raise requests.RequestException
        print(model_name, "API: ✅")
    except requests.RequestException:
        print(model_name, "API: ❌")
        print("\nError: OpenAI API is currently unavailable.\nPlease try again later.\n")
        exit(1)

    print("") # New row for readability

def connection_speedtest():
    st = speedtest.Speedtest()
    st.get_best_server()
    download_speed = f"{st.download() / 1_000_000:.2f}"
    upload_speed = f"{st.upload() / 1_000_000:.2f}"
    ping = f"{st.results.ping:.2f}"
    print(f"Download speed: {download_speed} Mbps\nUpload speed: {upload_speed} Mbps\nPing: {ping} ms\n")
    return download_speed, upload_speed, ping

def format_duration(seconds):
    hours = int(seconds) // 3600
    minutes = (int(seconds) % 3600) // 60
    seconds = round(seconds % 60, 3)

    if hours > 0:
        return f"{hours}h {minutes}min {seconds}s"
    elif minutes > 0:
        return f"{minutes}min {seconds}s"
    else:
        return f"{seconds}s"

def benchmark(yt_url, summary_length, keywords, kw_analysis_length):
    print("Downloading audio...")
    start_time = time.time()
    audio_filename = download_yt_audio(yt_url)
    download_time = time.time() - start_time
    print("✅ Finished in:", format_duration(download_time), "\n")

    print("Converting audio...")
    start_time = time.time()
    converted_audio_filename = convert_audio(audio_filename)
    conversion_time = time.time() - start_time
    print("✅ Finished in:", format_duration(conversion_time), "\n")

    print("Transcribing audio...")
    start_time = time.time()
    transcript, transcript_timestamped, transcript_filtered = transcribe_audio(converted_audio_filename, keywords)
    transcription_time = time.time() - start_time
    print("✅ Finished in:", format_duration(transcription_time), "for", len(transcript.split()), "words", "\n")

    print("Analyzing sentiment...")
    start_time = time.time()
    sentiment_results = analyze_sentiments(transcript_filtered)
    sentiment_analysis_time = time.time() - start_time
    print("✅ Finished in:", format_duration(sentiment_analysis_time), "\n")

    print("Summarizing transcript...")
    start_time = time.time()
    summary = summariza_batonga(transcript, summary_length, keywords, kw_analysis_length)
    summarization_time = time.time() - start_time
    print("✅ Finished in:", format_duration(summarization_time), "\n")

    os.remove(audio_filename)
    os.remove(converted_audio_filename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="This a performance benchmark script for YouTube video analysis.")
    parser.add_argument("yt_url", type=str, help="Link to the YouTube video.")
    parser.add_argument("summary_length", type=int, help="Desired summary length in sentences Format: int.")
    parser.add_argument("keywords", type=str, help="Keywords to analyze. Format like this: 'keyword1, keyword2'.")
    parser.add_argument("kw_analysis_length", type=int, help="Desired keyword analysis length in sentences. Format: int.")
    args = parser.parse_args()
    main(args)