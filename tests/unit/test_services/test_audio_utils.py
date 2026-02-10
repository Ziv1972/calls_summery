"""Tests for audio utilities."""

from src.utils.audio_utils import AUDIO_MIME_TYPES, get_content_type, is_audio_file


class TestGetContentType:
    """Test get_content_type function."""

    def test_mp3(self):
        assert get_content_type("song.mp3") == "audio/mpeg"

    def test_wav(self):
        assert get_content_type("recording.wav") == "audio/wav"

    def test_m4a(self):
        assert get_content_type("call.m4a") == "audio/x-m4a"

    def test_mp4(self):
        assert get_content_type("video.mp4") == "audio/mp4"

    def test_ogg(self):
        assert get_content_type("audio.ogg") == "audio/ogg"

    def test_webm(self):
        assert get_content_type("file.webm") == "audio/webm"

    def test_flac(self):
        assert get_content_type("music.flac") == "audio/flac"

    def test_unknown_extension(self):
        assert get_content_type("file.xyz") == "application/octet-stream"

    def test_no_extension(self):
        assert get_content_type("noext") == "application/octet-stream"

    def test_uppercase_extension(self):
        assert get_content_type("FILE.MP3") == "audio/mpeg"


class TestIsAudioFile:
    """Test is_audio_file function."""

    def test_audio_file(self):
        assert is_audio_file("test.mp3") is True

    def test_wav_file(self):
        assert is_audio_file("recording.wav") is True

    def test_non_audio_file(self):
        assert is_audio_file("document.pdf") is False

    def test_no_extension(self):
        assert is_audio_file("noext") is False

    def test_uppercase(self):
        assert is_audio_file("TEST.M4A") is True


class TestAudioMimeTypes:
    """Test AUDIO_MIME_TYPES dict."""

    def test_has_all_common_formats(self):
        expected = {".mp3", ".mp4", ".m4a", ".wav", ".ogg", ".webm", ".flac"}
        assert set(AUDIO_MIME_TYPES.keys()) == expected
