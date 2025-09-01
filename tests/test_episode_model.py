"""Tests for the Episode data model."""

import pytest
from datetime import datetime
from src.models.episode import Episode, EpisodeType, GameSeries


class TestEpisodeType:
    """Test EpisodeType enum."""
    
    def test_episode_type_values(self):
        """Test that EpisodeType has expected values."""
        assert EpisodeType.MAIN_SHOW.value == "main_show"
        assert EpisodeType.STEAM_TRAIN.value == "steam_train"
        assert EpisodeType.GRUMPCADE.value == "grumpcade"
        assert EpisodeType.COMPILATION.value == "compilation"
        assert EpisodeType.SPECIAL.value == "special"
        assert EpisodeType.LIVE.value == "live"


class TestGameSeries:
    """Test GameSeries enum."""
    
    def test_game_series_values(self):
        """Test that GameSeries has expected values."""
        assert GameSeries.SONIC_06.value == "Sonic '06"
        assert GameSeries.MARIO_MAKER.value == "Super Mario Maker"
        assert GameSeries.ZELDA.value == "The Legend of Zelda"
        assert GameSeries.POKEMON.value == "Pokemon"
        assert GameSeries.KIRBY.value == "Kirby"
        assert GameSeries.MEGAMAN.value == "Mega Man"


class TestEpisode:
    """Test Episode data class."""
    
    def test_episode_creation(self):
        """Test basic episode creation."""
        episode = Episode(
            episode_id="test_123",
            title="Test Episode",
            youtube_url="https://www.youtube.com/watch?v=test123",
            youtube_id="test123",
            game_name="Test Game"
        )
        
        assert episode.episode_id == "test_123"
        assert episode.title == "Test Episode"
        assert episode.youtube_url == "https://www.youtube.com/watch?v=test123"
        assert episode.youtube_id == "test123"
        assert episode.game_name == "Test Game"
        assert episode.episode_type == EpisodeType.MAIN_SHOW
        assert episode.hosts == ["Arin Hanson", "Dan Avidan"]
        assert episode.watched is False
    
    def test_episode_youtube_id_extraction(self):
        """Test automatic YouTube ID extraction from URL."""
        episode = Episode(
            episode_id="test_123",
            title="Test Episode",
            youtube_url="https://www.youtube.com/watch?v=abc123def",
            youtube_id="",  # Empty, should be extracted
            game_name="Test Game"
        )
        
        assert episode.youtube_id == "abc123def"
    
    def test_episode_youtube_id_extraction_various_formats(self):
        """Test YouTube ID extraction from various URL formats."""
        urls = [
            "https://www.youtube.com/watch?v=abc123def",
            "https://youtu.be/abc123def",
            "https://www.youtube.com/embed/abc123def",
            "https://www.youtube.com/v/abc123def"
        ]
        
        for url in urls:
            episode = Episode(
                episode_id="test_123",
                title="Test Episode",
                youtube_url=url,
                youtube_id="",
                game_name="Test Game"
            )
            assert episode.youtube_id == "abc123def"
    
    def test_episode_freetube_url(self):
        """Test FreeTube URL generation."""
        episode = Episode(
            episode_id="test_123",
            title="Test Episode",
            youtube_url="https://www.youtube.com/watch?v=test123",
            youtube_id="test123",
            game_name="Test Game"
        )
        
        assert episode.freetube_url == "freetube://https://www.youtube.com/watch?v=test123"
    
    def test_episode_short_title(self):
        """Test short title generation."""
        # Short title
        episode1 = Episode(
            episode_id="test_123",
            title="Short Title",
            youtube_url="https://www.youtube.com/watch?v=test123",
            youtube_id="test123",
            game_name="Test Game"
        )
        assert episode1.short_title == "Short Title"
        
        # Long title
        long_title = "A" * 70  # 70 characters
        episode2 = Episode(
            episode_id="test_123",
            title=long_title,
            youtube_url="https://www.youtube.com/watch?v=test123",
            youtube_id="test123",
            game_name="Test Game"
        )
        assert len(episode2.short_title) == 60
        assert episode2.short_title.endswith("...")
    
    def test_episode_formatted_duration(self):
        """Test duration formatting."""
        # Minutes only
        episode1 = Episode(
            episode_id="test_123",
            title="Test Episode",
            youtube_url="https://www.youtube.com/watch?v=test123",
            youtube_id="test123",
            game_name="Test Game",
            duration_seconds=1250  # 20:50
        )
        assert episode1.formatted_duration == "20:50"
        
        # Hours and minutes
        episode2 = Episode(
            episode_id="test_123",
            title="Test Episode",
            youtube_url="https://www.youtube.com/watch?v=test123",
            youtube_id="test123",
            game_name="Test Game",
            duration_seconds=7325  # 2:02:05
        )
        assert episode2.formatted_duration == "2:02:05"
        
        # No duration
        episode3 = Episode(
            episode_id="test_123",
            title="Test Episode",
            youtube_url="https://www.youtube.com/watch?v=test123",
            youtube_id="test123",
            game_name="Test Game"
        )
        assert episode3.formatted_duration == "Unknown"
    
    def test_episode_upload_date_formatted(self):
        """Test upload date formatting."""
        test_date = datetime(2023, 12, 25)
        episode = Episode(
            episode_id="test_123",
            title="Test Episode",
            youtube_url="https://www.youtube.com/watch?v=test123",
            youtube_id="test123",
            game_name="Test Game",
            upload_date=test_date
        )
        
        assert episode.upload_date_formatted == "December 25, 2023"
        
        # No date
        episode_no_date = Episode(
            episode_id="test_123",
            title="Test Episode",
            youtube_url="https://www.youtube.com/watch?v=test123",
            youtube_id="test123",
            game_name="Test Game"
        )
        assert episode_no_date.upload_date_formatted == "Unknown"
    
    def test_episode_to_dict(self):
        """Test episode serialization to dictionary."""
        test_date = datetime(2023, 12, 25)
        episode = Episode(
            episode_id="test_123",
            title="Test Episode",
            youtube_url="https://www.youtube.com/watch?v=test123",
            youtube_id="test123",
            game_name="Test Game",
            game_series=GameSeries.SONIC_06,
            episode_type=EpisodeType.MAIN_SHOW,
            upload_date=test_date,
            tags=["test", "gaming"],
            hosts=["Arin Hanson", "Dan Avidan"],
            guests=["Guest Host"]
        )
        
        episode_dict = episode.to_dict()
        
        assert episode_dict["episode_id"] == "test_123"
        assert episode_dict["title"] == "Test Episode"
        assert episode_dict["game_series"] == "Sonic '06"
        assert episode_dict["episode_type"] == "main_show"
        assert episode_dict["upload_date"] == "2023-12-25T00:00:00"
        assert episode_dict["tags"] == ["test", "gaming"]
        assert episode_dict["hosts"] == ["Arin Hanson", "Dan Avidan"]
        assert episode_dict["guests"] == ["Guest Host"]
    
    def test_episode_from_dict(self):
        """Test episode deserialization from dictionary."""
        episode_dict = {
            "episode_id": "test_123",
            "title": "Test Episode",
            "youtube_url": "https://www.youtube.com/watch?v=test123",
            "youtube_id": "test123",
            "game_name": "Test Game",
            "game_series": "Sonic '06",
            "episode_type": "main_show",
            "upload_date": "2023-12-25T00:00:00",
            "tags": ["test", "gaming"],
            "hosts": ["Arin Hanson", "Dan Avidan"],
            "guests": ["Guest Host"],
            "watched": True,
            "rating": 5,
            "notes": "Great episode!"
        }
        
        episode = Episode.from_dict(episode_dict)
        
        assert episode.episode_id == "test_123"
        assert episode.title == "Test Episode"
        assert episode.game_series == GameSeries.SONIC_06
        assert episode.episode_type == EpisodeType.MAIN_SHOW
        assert episode.upload_date == datetime(2023, 12, 25)
        assert episode.tags == ["test", "gaming"]
        assert episode.hosts == ["Arin Hanson", "Dan Avidan"]
        assert episode.guests == ["Guest Host"]
        assert episode.watched is True
        assert episode.rating == 5
        assert episode.notes == "Great episode!"
    
    def test_episode_string_representation(self):
        """Test episode string representation."""
        episode = Episode(
            episode_id="test_123",
            title="Test Episode",
            youtube_url="https://www.youtube.com/watch?v=test123",
            youtube_id="test123",
            game_name="Test Game",
            episode_number=42
        )
        
        assert str(episode) == "Episode 42: Test Episode (Test Game)"
        
        # No episode number
        episode_no_num = Episode(
            episode_id="test_123",
            title="Test Episode",
            youtube_url="https://www.youtube.com/watch?v=test123",
            youtube_id="test123",
            game_name="Test Game"
        )
        assert str(episode_no_num) == "Episode N/A: Test Episode (Test Game)"
    
    def test_episode_repr(self):
        """Test episode representation."""
        episode = Episode(
            episode_id="test_123",
            title="Test Episode",
            youtube_url="https://www.youtube.com/watch?v=test123",
            youtube_id="test123",
            game_name="Test Game"
        )
        
        repr_str = repr(episode)
        assert "Episode(" in repr_str
        assert "episode_id='test_123'" in repr_str
        assert "title='Test Episode'" in repr_str
        assert "game_name='Test Game'" in repr_str
