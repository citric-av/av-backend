import pytest
from unittest.mock import patch, Mock, MagicMock
from modules import download_yt_audio, convert_audio, filter_sentences_with_context, transcribe_audio, summariza_batonga, analyze_sentiments
from pytube.exceptions import RegexMatchError, VideoUnavailable

# Test for successful audio download
def test_download_yt_audio_success():
    with patch('modules.YouTube') as mock_youtube:
        # Mock the YouTube object and its method chain
        mock_audio_stream = Mock()
        mock_audio_stream.default_filename = 'test_audio.mp4'
        mock_audio_stream.download.return_value = None  # download() doesn't return anything
        mock_youtube.return_value.streams.filter.return_value.first.return_value = mock_audio_stream

        # Act
        result = download_yt_audio('https://www.youtube.com/watch?v=dQw4w9WgXcQ')

        # Assert
        assert result == 'test_audio.mp4'
        mock_youtube.assert_called_once_with('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        mock_audio_stream.download.assert_called_once_with(filename='test_audio.mp4')

# Test for handling invalid URL
def test_download_yt_audio_regex_error():
    with patch('modules.YouTube', side_effect=RegexMatchError("pattern", "Regex match error")):
        # Act and Assert
        with pytest.raises(RegexMatchError):
            download_yt_audio('invalid_url')

# Test for handling non-existent video
def test_download_yt_audio_video_unavailable():
    with patch('modules.YouTube', side_effect=VideoUnavailable("Video unavailable")):
        # Act and Assert
        with pytest.raises(VideoUnavailable):
            download_yt_audio('https://www.youtube.com/watch?v=non_existent_video')

# Test for successful audio conversion
def test_convert_audio():
    # Mock AudioSegment and its chain of methods
    with patch('modules.AudioSegment') as mock_audio_segment:
        # Setting up the mock object and its method returns
        mock_audio_segment.from_file.return_value = mock_audio_segment
        mock_audio_segment.set_channels.return_value = mock_audio_segment
        mock_audio_segment.set_frame_rate.return_value = mock_audio_segment

        # The input and expected output filenames
        input_filename = 'test_audio.mp4'
        expected_output_filename = 'test_audio.mp4_converted.wav'

        # Act
        result = convert_audio(input_filename)

        # Assert
        assert result == expected_output_filename
        mock_audio_segment.from_file.assert_called_once_with(input_filename, format="mp4")
        mock_audio_segment.set_channels.assert_called_once_with(1)
        mock_audio_segment.set_frame_rate.assert_called_once_with(16000)
        mock_audio_segment.export.assert_called_once_with(expected_output_filename, format="wav")

# Test for filtered sentences correct output
def test_filter_sentences_with_context():
    # Input data
    transcript_timestamped = [
        {"start": 0, "end": 14, "text": "Wow, what an audience."},
        {"start": 14, "end": 18, "text": "But if I'm being honest, I don't care what you think of my talk."},
        {"start": 18, "end": 19, "text": "I don't."}
    ]
    keywords = 'talk'

    # Expected output
    expected_filtered_sentences = [
        {
            "end": 19,
            "start": 0,
            "text": "... Wow, what an audience. But if I'm being honest, I don't care what you think of my talk. I don't. ..."
        }
    ]

    # Act
    result = filter_sentences_with_context(transcript_timestamped, keywords)

    # Assert
    assert result == expected_filtered_sentences, "The filtered sentences do not match the expected output"

# Test for successful transcription
def test_transcribe_audio():
    # Mock transcript_sentences data based on your provided JSON structure
    mock_transcript_sentences = [
        {
            "avg_logprob": -0.24279173826559997,
            "compression_ratio": 1.578616352201258,
            "end": 14.68,
            "id": 0,
            "no_speech_prob": 0.06905094534158707,
            "seek": 0,
            "start": 0.0,
            "temperature": 0.0,
            "text": "Wow, what an audience.",
            "tokens": [50364, 3153, 11, 437, 364, 4034, 13, 51098]
        },
        {
            "avg_logprob": -0.24279173826559997,
            "compression_ratio": 1.578616352201258,
            "end": 18.2,
            "id": 1,
            "no_speech_prob": 0.06905094534158707,
            "seek": 0,
            "start": 14.68,
            "temperature": 0.0,
            "text": "But if I'm being honest, I don't care what you think of my talk.",
            "tokens": [51098, 583, 498, 286, 478, 885, 3245, 11, 286, 500, 380, 1127, 437, 291, 519, 295, 452, 751, 13, 51274]
        },
        {
            "avg_logprob": -0.24279173826559997,
            "compression_ratio": 1.578616352201258,
            "end": 19.2,
            "id": 2,
            "no_speech_prob": 0.06905094534158707,
            "seek": 0,
            "start": 18.2,
            "temperature": 0.0,
            "text": "I don't.",
            "tokens": [51274, 286, 500, 380, 13, 51324]
        }
    ]

    # Mocked result from whisper model
    mock_transcribe_result = {
        "text": "Full transcript text",
        "segments": mock_transcript_sentences
    }

    # Mock filter_sentences_with_context to return a specific output
    mock_filtered_sentences = [
        {
            "end": 19,
            "start": 0,
            "text": "... Wow, what an audience. But if I'm being honest, I don't care what you think of my talk. I don't. ..."
        }
    ]

    with patch('modules.whisper.load_model') as mock_load_model, \
         patch('modules.filter_sentences_with_context', return_value=mock_filtered_sentences) as mock_filter:
        # Setting up the mock model
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        mock_model.transcribe.return_value = mock_transcribe_result

        # The input filename and keywords
        converted_audio_filename = 'test_audio.wav'
        keywords = 'talk'

        # Act
        transcript, transcript_timestamped, transcript_filtered = transcribe_audio(converted_audio_filename, keywords)

        # Assert
        assert transcript == "Full transcript text"
        
        # Check transcript_timestamped
        expected_timestamped = [
            {"start": 0, "end": 14, "text": "Wow, what an audience."},
            {"start": 14, "end": 18, "text": "But if I'm being honest, I don't care what you think of my talk."},
            {"start": 18, "end": 19, "text": "I don't."}
        ]
        assert transcript_timestamped == expected_timestamped

        # Check transcript_filtered
        assert transcript_filtered == mock_filtered_sentences

        # Ensure mock methods were called correctly
        mock_load_model.assert_called_once_with("small")
        mock_model.transcribe.assert_called_once_with(converted_audio_filename)
        mock_filter.assert_called_once_with(expected_timestamped, keywords)

# Test for sentiment analysis correct output
def test_analyze_sentiments():
    # Input data
    mock_filtered_sentences = [
        {
            "end": 19,
            "start": 0,
            "text": "... Wow, what an audience. But if I'm being honest, I don't care what you think of my talk. I don't. ..."
        }
    ]

    # Act
    result = analyze_sentiments(mock_filtered_sentences)

    # Assert
    assert isinstance(result, list), "The result should be a list"
    assert len(result) == len(mock_filtered_sentences), "The result list should have the same length as the input"
    for sentiment_result in result:
        assert "text" in sentiment_result, "Each result should have a 'text' field"
        assert "sentiment" in sentiment_result, "Each result should have a 'sentiment' field"
        assert all(key in sentiment_result["sentiment"] for key in ["compound", "neg", "neu", "pos"]), \
            "The sentiment field should contain 'compound', 'neg', 'neu', 'pos' keys"
        
# Test for successful summarization
def test_summariza_batonga():
    mock_response_content = "Mocked summary and keyword analysis."
    
    with patch('modules.load_dotenv'), \
         patch('modules.os.getenv', return_value='mock_api_key'), \
         patch('modules.OpenAI') as mock_openai:
        
        # Mocking the OpenAI client and its response
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = Mock(choices=[Mock(message=Mock(content=mock_response_content))])

        # The input parameters
        text = "Sample video transcript"
        length = 3
        keywords = "keyword1, keyword2"
        kw_analysis_length = 2

        # Act
        result = summariza_batonga(text, length, keywords, kw_analysis_length)

        # Assert
        assert isinstance(result, str), "The function should return a string"
        assert result == mock_response_content, "The function should return the mocked response content"

        # Verify that the OpenAI client was called correctly
        mock_client.chat.completions.create.assert_called_once()