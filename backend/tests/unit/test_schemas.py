"""
Unit tests for Pydantic data models
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.schemas import (
    StoryRequest,
    ChapterContent,
    AgentProgress,
    StoryState,
    WebSocketMessage,
    StoryGenerateResponse,
    StoryResponse,
    AgentType,
    AgentStatus,
    StoryStyle,
)


class TestStoryRequest:
    """Test StoryRequest model"""

    def test_valid_request(self):
        """Test valid story request"""
        request = StoryRequest(
            theme="This is a story about a brave little rabbit who travels through the forest to find the lost treasure"
        )
        assert len(request.theme) >= 30
        assert request.style is None
        assert request.chapter_count == 4  # default value

    def test_request_with_style(self):
        """Test request with style specified"""
        request = StoryRequest(
            theme="This is a story about a brave little rabbit who travels through the forest to find the lost treasure",
            style=StoryStyle.ADVENTURE,
            chapter_count=6
        )
        assert request.style == StoryStyle.ADVENTURE
        assert request.chapter_count == 6

    def test_theme_too_short(self):
        """Test theme validation - too short"""
        with pytest.raises(ValidationError) as exc_info:
            StoryRequest(theme="Too short")
        assert "theme" in str(exc_info.value)

    def test_theme_too_long(self):
        """Test theme validation - too long"""
        with pytest.raises(ValidationError) as exc_info:
            StoryRequest(theme="x" * 2001)
        assert "theme" in str(exc_info.value)

    def test_chapter_count_too_small(self):
        """Test chapter_count validation - too small"""
        with pytest.raises(ValidationError) as exc_info:
            StoryRequest(
                theme="This is a story about a brave little rabbit who travels through the forest to find the lost treasure",
                chapter_count=0
            )
        assert "chapter_count" in str(exc_info.value)

    def test_chapter_count_too_large(self):
        """Test chapter_count validation - too large"""
        with pytest.raises(ValidationError) as exc_info:
            StoryRequest(
                theme="This is a story about a brave little rabbit who travels through the forest to find the lost treasure",
                chapter_count=9
            )
        assert "chapter_count" in str(exc_info.value)


class TestChapterContent:
    """Test ChapterContent model"""

    def test_valid_chapter(self):
        """Test valid chapter content"""
        chapter = ChapterContent(
            chapter_id=1,
            title="Chapter 1: The Adventure Begins",
            text="Once upon a time, there was a brave little rabbit..."
        )
        assert chapter.chapter_id == 1
        assert chapter.title == "Chapter 1: The Adventure Begins"
        assert chapter.text == "Once upon a time, there was a brave little rabbit..."
        assert chapter.image_url is None
        assert chapter.image_prompt is None

    def test_chapter_with_image(self):
        """Test chapter with image data"""
        chapter = ChapterContent(
            chapter_id=1,
            title="Chapter 1",
            text="Content",
            image_url="https://oaidalleapiprodscus.blob.core.windows.net/private/xxx.png",
            image_prompt="a brave rabbit in the forest"
        )
        assert chapter.image_url is not None
        assert chapter.image_prompt is not None


class TestAgentProgress:
    """Test AgentProgress model"""

    def test_valid_progress(self):
        """Test valid agent progress"""
        progress = AgentProgress(
            agent_id="writer-1",
            agent_type=AgentType.WRITER,
            chapter_id=1,
            status=AgentStatus.RUNNING,
            progress=0.5,
            elapsed_time=2.5
        )
        assert progress.agent_id == "writer-1"
        assert progress.agent_type == AgentType.WRITER
        assert progress.status == AgentStatus.RUNNING
        assert progress.progress == 0.5

    def test_progress_bounds(self):
        """Test progress value bounds"""
        # Valid: 0.0
        progress = AgentProgress(
            agent_id="test",
            agent_type=AgentType.PLANNER,
            status=AgentStatus.PENDING,
            progress=0.0
        )
        assert progress.progress == 0.0

        # Valid: 1.0
        progress = AgentProgress(
            agent_id="test",
            agent_type=AgentType.PLANNER,
            status=AgentStatus.COMPLETED,
            progress=1.0
        )
        assert progress.progress == 1.0

        # Invalid: negative
        with pytest.raises(ValidationError):
            AgentProgress(
                agent_id="test",
                agent_type=AgentType.PLANNER,
                status=AgentStatus.PENDING,
                progress=-0.1
            )

        # Invalid: > 1.0
        with pytest.raises(ValidationError):
            AgentProgress(
                agent_id="test",
                agent_type=AgentType.PLANNER,
                status=AgentStatus.PENDING,
                progress=1.1
            )

    def test_progress_with_error(self):
        """Test progress with error message"""
        progress = AgentProgress(
            agent_id="test",
            agent_type=AgentType.IMAGE_GEN,
            status=AgentStatus.FAILED,
            progress=0.0,
            error_message="API timeout"
        )
        assert progress.status == AgentStatus.FAILED
        assert progress.error_message == "API timeout"


class TestStoryState:
    """Test StoryState model"""

    def test_valid_state(self):
        """Test valid story state"""
        now = datetime.now()
        state = StoryState(
            session_id="test-session-123",
            theme="Test Theme",
            status="running",
            created_at=now,
            updated_at=now
        )
        assert state.session_id == "test-session-123"
        assert state.theme == "Test Theme"
        assert state.status == "running"
        assert len(state.chapters) == 0
        assert len(state.agent_progress) == 0

    def test_state_with_chapters(self):
        """Test state with chapters"""
        now = datetime.now()
        chapters = [
            ChapterContent(
                chapter_id=1,
                title="Chapter 1",
                text="Content 1"
            ),
            ChapterContent(
                chapter_id=2,
                title="Chapter 2",
                text="Content 2"
            )
        ]
        state = StoryState(
            session_id="test",
            theme="Theme",
            status="completed",
            chapters=chapters,
            created_at=now,
            updated_at=now,
            total_time=15.5
        )
        assert len(state.chapters) == 2
        assert state.total_time == 15.5


class TestWebSocketMessage:
    """Test WebSocketMessage model"""

    def test_valid_message(self):
        """Test valid WebSocket message"""
        message = WebSocketMessage(
            event_id="evt-123",
            type="agent_started",
            timestamp=1234567890.0,
            session_id="session-123",
            data={"agent_id": "writer-1", "status": "running"}
        )
        assert message.event_id == "evt-123"
        assert message.type == "agent_started"
        assert message.session_id == "session-123"
        assert "agent_id" in message.data


class TestStoryGenerateResponse:
    """Test StoryGenerateResponse model"""

    def test_valid_response(self):
        """Test valid generation response"""
        response = StoryGenerateResponse(
            session_id="session-123",
            message="Story generation started",
            status="pending"
        )
        assert response.session_id == "session-123"
        assert response.message == "Story generation started"
        assert response.status == "pending"

    def test_different_statuses(self):
        """Test different status values"""
        statuses = ["pending", "running", "completed", "failed"]
        for status in statuses:
            response = StoryGenerateResponse(
                session_id="session-123",
                message=f"Status: {status}",
                status=status
            )
            assert response.status == status


class TestStoryResponse:
    """Test StoryResponse model"""

    def test_valid_story_response(self):
        """Test valid story response"""
        chapters = [
            ChapterContent(
                chapter_id=1,
                title="Chapter 1",
                text="Content"
            )
        ]
        response = StoryResponse(
            session_id="session-123",
            theme="Theme",
            chapters=chapters,
            total_time=10.5,
            metadata={"version": "1.0"}
        )
        assert response.session_id == "session-123"
        assert len(response.chapters) == 1
        assert response.total_time == 10.5
        assert "version" in response.metadata

