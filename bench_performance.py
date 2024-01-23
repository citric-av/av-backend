try:
    import os
    from modules import download_yt_audio, convert_audio, transcribe_audio, summariza_batonga, analyze_sentiments
    from pytube import YouTube
    import time
    import datetime
    import speedtest
    import requests
    import argparse
    from dotenv import load_dotenv
    import csv
    import psutil
    import cpuinfo
    import GPUtil
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

    print(make_bold("\n🖥️ System specs:\n"))
    cpu_brand, cpu_base_clock, cpu_cores, cpu_threads = get_cpu_info()
    ram_total = get_ram_info()
    gpu_name, gpu_memory = get_gpu_info()
    print(f"CPU: {make_bold(cpu_brand)} @ {make_bold(cpu_base_clock)}")
    print(f"CPU Cores: {make_bold(cpu_cores)} physical, {make_bold(cpu_threads)} logical")
    print(f"GPU: {make_bold(gpu_name)}")
    print(f"GPU Memory: {make_bold(gpu_memory)}MB")
    print(f"RAM: {make_bold(ram_total)}MB\n")

    print(make_bold("🌐 Running network tests...\n"))
    check_connection()
    check_endpoints()

    print(make_bold("⚡ Checking internet speed...\n"))
    speedtest_performed = False
    try:
        download_speed, upload_speed, ping = connection_speedtest()
        speedtest_performed = True
    except Exception as e:
        print(f"Error: Speedtest unavailable - ({e}).\nResults based on your internet speed will be hidden.\n")
        download_speed = 1
        upload_speed = 1
        ping = 1

    try:
        yt = YouTube(yt_url)
        print("Youtube Video:", make_bold(yt.title))
        print("Video Length:", make_bold(format_duration(yt.length)),"\n")
    except:
        print("Error: Invalid YouTube URL.\nPlease check the link and try again.\n")
        exit(1)

    print(make_bold("📊 Starting benchmark...\n"))
    download_time, conversion_time, transcription_time, sentiment_analysis_time, summarization_time, transcript, summary = benchmark(yt_url, summary_length, keywords, kw_analysis_length)

    print(make_bold("📈 Benchmark results:"))
    transcript_word_count = len(transcript.split())
    summary_word_count = len(summary.split())
    keyword_count = len(keywords.split(","))
    video_size_mb = (download_speed * download_time) / 8  # Convert Mbps to MBps and calculate size
    one_minute_size_mb = video_size_mb / yt.length * 60
    one_hour_size_mb = one_minute_size_mb * 60
    download_time_1_min = one_minute_size_mb / download_speed * 8
    download_time_1_hour = one_hour_size_mb / download_speed * 8
    transcript_word_count = len(transcript.split())
    words_per_minute = transcript_word_count / (transcription_time / 60)
    time_for_1000_words = 1000 / words_per_minute * 60
    time_for_1000_word_summary = summarization_time / transcript_word_count * 1000

    if speedtest_performed:
        print(make_bold("\nConnection Speed:"))
        print(f" - Your download speed: {make_bold(download_speed)} Mbps")
        print(f" - Time taken to download {make_bold(format_duration(yt.length))} of audio: {make_bold(format_duration(download_time))}")
        print(f" - Estimated time for 1 minute of audio: {make_bold(format_duration(download_time_1_min))}")
        print(f" - Estimated time for 1 hour of audio: {make_bold(format_duration(download_time_1_hour))}")

    print(make_bold("\nTranscription:"))
    print(f" - Total words transcribed: {make_bold(transcript_word_count)}")
    print(f" - Words per minute: {make_bold(round(words_per_minute, 2))}")
    print(f" - Estimated time for 1000 words: {make_bold(format_duration(time_for_1000_words))}")

    print(make_bold("\nSummary:"))
    print(f" - Summary settings: {make_bold(summary_length)} sentences, {make_bold(keyword_count)} keywords, {make_bold(kw_analysis_length)} sentences per keyword")
    print(f" - Time taken for summarizing {make_bold(transcript_word_count)} words into {make_bold(summary_length + keyword_count * kw_analysis_length)} sentences: {make_bold(format_duration(summarization_time))}")
    print(f" - Estimated time for summarizing 1000 words with the same settings: {make_bold(format_duration(time_for_1000_word_summary))}")
    print("\nNote: Summary speed is not dependent on hardware since it is currently done over OpenAI's API.")

    ask_export_to_csv(download_speed, upload_speed, ping, download_time, yt.length, download_time_1_min, download_time_1_hour, transcription_time, transcript_word_count, words_per_minute, time_for_1000_words, summarization_time, summary_length, time_for_1000_word_summary, keyword_count, kw_analysis_length, cpu_brand, cpu_base_clock, cpu_cores, cpu_threads, ram_total, gpu_name, gpu_memory)
    print(make_bold("\n🎉 Benchmark complete! 🎉\n"))

def make_bold(text):
    return f"\033[1m{text}\033[0m"

def greeting():
    welcome_message = make_bold("\n👋 Welcome to our performance benchmark!\n")
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
    download_speed = float(f"{st.download() / 1_000_000:.2f}")
    upload_speed = float(f"{st.upload() / 1_000_000:.2f}")
    ping = f"{st.results.ping:.2f}"
    print(f"Download speed: {download_speed} Mbps\nUpload speed: {upload_speed} Mbps\nPing: {ping} ms\n")
    return download_speed, upload_speed, ping

def format_duration(seconds):
    hours = int(seconds) // 3600
    minutes = (int(seconds) % 3600) // 60
    seconds = round(seconds % 60, 3)

    if hours > 0:
        return f"{hours}h {minutes}min {int(seconds)}s"
    elif minutes > 0:
        return f"{minutes}min {int(seconds)}s"
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
    print("✅ Finished in:", format_duration(transcription_time), "\n")

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

    return download_time, conversion_time, transcription_time, sentiment_analysis_time, summarization_time, transcript, summary

def ask_export_to_csv(download_speed, upload_speed, ping, download_time, yt_length, download_time_1_min, download_time_1_hour, transcription_time, transcript_word_count, words_per_minute, time_for_1000_words, summarization_time, summary_length, time_for_1000_word_summary, keyword_count, kw_analysis_length, cpu_brand, cpu_base_clock, cpu_cores, cpu_threads, ram_total, gpu_name, gpu_memory):
    response = input("\nDo you want to export the results as a CSV file? (y/n): ")
    if response.lower() == 'y':
        current_datetime = datetime.datetime.now()
        folder_path = './benchmarks/'
        filename = f"bench_performance{current_datetime.strftime('%Y%m%d-%H%M%S')}.csv"
        export_to_csv(folder_path, filename, download_speed, upload_speed, ping, download_time, yt_length, download_time_1_min, download_time_1_hour, transcription_time, transcript_word_count, words_per_minute, time_for_1000_words, summarization_time, summary_length, time_for_1000_word_summary, keyword_count, kw_analysis_length, cpu_brand, cpu_base_clock, cpu_cores, cpu_threads, ram_total, gpu_name, gpu_memory)
        print(f"\nResults exported to {filename}")
    else:
        print("\nCSV not exported.")

def export_to_csv(folder_path, filename, download_speed, upload_speed, ping, download_time, yt_length, download_time_1_min, download_time_1_hour, transcription_time, transcript_word_count, words_per_minute, time_for_1000_words, summarization_time, summary_length, time_for_1000_word_summary, keyword_count, kw_analysis_length, cpu_brand, cpu_base_clock, cpu_cores, cpu_threads, ram_total, gpu_name, gpu_memory):
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    full_path = folder_path + filename

    with open(full_path, 'w', newline='') as file:
        writer = csv.writer(file)

        writer.writerow(['Metric', 'Raw Data', 'Calculated Estimate'])

        writer.writerow(['Download Speed (Mbps)', download_speed, ''])
        writer.writerow(['Upload Speed (Mbps)', upload_speed, ''])
        writer.writerow(['Ping (ms)', ping, ''])
        writer.writerow(['Download Time for Video (s)', download_time, f'{yt_length} seconds video'])
        writer.writerow(['Estimated Download Time for 1 Min of Audio (s)', '', download_time_1_min])
        writer.writerow(['Estimated Download Time for 1 Hour of Audio (s)', '', download_time_1_hour])
        writer.writerow(['Transcription Time (s)', transcription_time, ''])
        writer.writerow(['Total Words in Transcript', transcript_word_count, ''])
        writer.writerow(['Words Per Minute', '', words_per_minute])
        writer.writerow(['Estimated Time for 1000 Words (s)', '', time_for_1000_words])
        writer.writerow(['Summarization Time (s)', summarization_time, f'for {summary_length} sentences'])
        writer.writerow(['Estimated Time for Summarizing 1000 Words (s)', '', time_for_1000_word_summary])
        writer.writerow(['Summary Length (sentences)', summary_length, ''])
        writer.writerow(['Keyword Count', keyword_count, ''])
        writer.writerow(['Sentences per Keyword', kw_analysis_length, ''])
        writer.writerow(['CPU Name', cpu_brand, ''])
        writer.writerow(['CPU Base Clock', cpu_base_clock, ''])
        writer.writerow(['CPU Cores', cpu_cores, ''])
        writer.writerow(['CPU Threads', cpu_threads, ''])
        writer.writerow(['RAM Total (MB)', ram_total, ''])
        writer.writerow(['GPU Name', gpu_name, ''])
        writer.writerow(['GPU Memory (MB)', gpu_memory, ''])

def get_system_info():
    try:
        cpu = cpuinfo.get_cpu_info()
        cpu_brand = cpu.get("brand_raw", "N/A")
        cpu_base_clock = cpu.get("hz_advertised_friendly", "N/A")
        cpu_cores = psutil.cpu_count(logical=False)
        cpu_threads = psutil.cpu_count(logical=True)

        ram = psutil.virtual_memory()
        ram_total = f"{ram.total/1024/1024:.2f}"

        gpu = GPUtil.getGPUs()[0]
        gpu_name = gpu.name
        gpu_memory = gpu.memoryTotal

        return cpu_brand, cpu_base_clock, cpu_cores, cpu_threads, ram_total, gpu_name, gpu_memory
    except Exception as e:
        print(f"Error: Could not get system specs - {e}")
        return 
    
def get_cpu_info():
    try:
        cpu = cpuinfo.get_cpu_info()
        cpu_brand = cpu.get("brand_raw", "N/A")
        cpu_base_clock = cpu.get("hz_advertised_friendly", "N/A")
        cpu_cores = psutil.cpu_count(logical=False)
        cpu_threads = psutil.cpu_count(logical=True)
        return cpu_brand, cpu_base_clock, cpu_cores, cpu_threads
    except Exception as e:
        print(f"Error: Could not get CPU info - {e}")
        return "N/A", "N/A", "N/A", "N/A"
    
def get_ram_info():
    try:
        ram = psutil.virtual_memory()
        ram_total = f"{ram.total/1024/1024:.2f}"
        return ram_total
    except Exception as e:
        print(f"Error: Could not get RAM info - {e}")
        return "N/A"
    
def get_gpu_info():
    try:
        gpu = GPUtil.getGPUs()[0]
        gpu_name = gpu.name
        gpu_memory = gpu.memoryTotal
        return gpu_name, gpu_memory
    except Exception as e:
        print(f"Error: Could not get GPU info - {e}")
        return "N/A", "N/A"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="This a performance benchmark script for YouTube video analysis.")
    parser.add_argument("yt_url", type=str, help="Link to the YouTube video.")
    parser.add_argument("summary_length", type=int, help="Desired summary length in sentences Format: int.")
    parser.add_argument("keywords", type=str, help="Keywords to analyze. Format like this: 'keyword1, keyword2'.")
    parser.add_argument("kw_analysis_length", type=int, help="Desired keyword analysis length in sentences. Format: int.")
    args = parser.parse_args()
    main(args)