"""
Integration tests for AI services with real API keys
These tests require actual API keys to be set in environment variables.
Skip if API keys are not available.
"""
import pytest
import os
from app.services.ai_services.text_generator import get_text_generator
from app.services.ai_services.image_generator import get_image_generator
from app.core.config import settings


# Check if API keys are available
HAS_AWS_CREDENTIALS = bool(
    os.getenv("AWS_ACCESS_KEY") or getattr(settings, "AWS_ACCESS_KEY", None)
) and bool(
    os.getenv("AWS_SECRET_KEY") or getattr(settings, "AWS_SECRET_KEY", None)
)

HAS_OPENAI_KEY = bool(
    os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
)

HAS_STABILITY_KEY = bool(
    os.getenv("STABILITY_API_KEY") or getattr(settings, "STABILITY_API_KEY", None)
)


@pytest.mark.integration
class TestTextGeneratorIntegration:
    """Integration tests for text generation with real API"""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not (HAS_AWS_CREDENTIALS and HAS_OPENAI_KEY),
        reason="AWS credentials and OpenAI API key required"
    )
    async def test_text_generator_real_api(self):
        """Test text generation with real API calls"""
        generator = get_text_generator()
        
        prompt = "Write a short children's story (2-3 sentences) about a brave rabbit."
        
        result = await generator.generate(
            prompt,
            temperature=0.7,
            max_tokens=200
        )
        
        # Verify response format
        assert isinstance(result, str)
        assert len(result) > 0
        assert len(result.strip()) > 0
        
        # Verify content quality (basic checks)
        assert len(result) < 1000  # Should be reasonable length
        print(f"\nGenerated text: {result}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not (HAS_AWS_CREDENTIALS and HAS_OPENAI_KEY),
        reason="AWS credentials and OpenAI API key required"
    )
    async def test_text_generator_story_format(self):
        """Test that generated text is suitable for story format"""
        generator = get_text_generator()
        
        prompt = """Write a children's story chapter about a rabbit exploring a forest.
        Requirements:
        - 3-5 sentences
        - Age-appropriate language
        - Engaging narrative
        - Clear beginning and end"""
        
        result = await generator.generate(
            prompt,
            temperature=0.8,
            max_tokens=300
        )
        
        # Verify format
        assert isinstance(result, str)
        assert len(result) > 50  # Should have substantial content
        
        # Check for story-like characteristics
        sentences = result.split('.')
        assert len(sentences) >= 2  # Should have multiple sentences
        
        print(f"\nStory chapter: {result}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not (HAS_AWS_CREDENTIALS and HAS_OPENAI_KEY),
        reason="AWS credentials and OpenAI API key required"
    )
    async def test_text_generator_fallback_mechanism(self):
        """Test fallback mechanism when primary fails"""
        # This test verifies that fallback works
        # In real scenario, if primary fails, fallback should be used
        generator = get_text_generator()
        
        prompt = "Write a simple sentence about a cat."
        
        result = await generator.generate(prompt, temperature=0.7)
        
        # Should get a result from either primary or fallback
        assert isinstance(result, str)
        assert len(result) > 0
        print(f"\nResult (from primary or fallback): {result}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not HAS_OPENAI_KEY,
        reason="OpenAI API key required"
    )
    async def test_openai_generator_direct(self):
        """Test OpenAI generator directly"""
        from app.services.ai_services.text_generator import OpenAIGenerator
        
        generator = OpenAIGenerator()
        
        prompt = "Write one sentence about a dog."
        
        result = await generator.generate(prompt, temperature=0.7, max_tokens=50)
        
        assert isinstance(result, str)
        assert len(result) > 0
        print(f"\nOpenAI result: {result}")


@pytest.mark.integration
class TestImageGeneratorIntegration:
    """Integration tests for image generation with real API"""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not (HAS_STABILITY_KEY and HAS_OPENAI_KEY),
        reason="Stability API key and OpenAI API key required"
    )
    async def test_image_generator_real_api(self):
        """Test image generation with real API calls"""
        generator = get_image_generator()
        
        prompt = "a brave rabbit in a magical forest, children's book illustration"
        
        result = await generator.generate(prompt, style="watercolor")
        
        # Verify response format
        assert isinstance(result, str)
        assert result.startswith("data:image/")
        assert "base64," in result
        
        # Verify base64 data exists
        base64_part = result.split("base64,")[1]
        assert len(base64_part) > 100  # Should have substantial base64 data
        
        print(f"\nImage data URI length: {len(result)} characters")
        print(f"Image format: {result[:50]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not (HAS_STABILITY_KEY and HAS_OPENAI_KEY),
        reason="Stability API key and OpenAI API key required"
    )
    async def test_image_generator_different_styles(self):
        """Test image generation with different styles"""
        generator = get_image_generator()
        
        base_prompt = "a friendly rabbit reading a book"
        styles = ["cartoon", "watercolor", "realistic"]
        
        for style in styles:
            result = await generator.generate(base_prompt, style=style)
            
            assert isinstance(result, str)
            assert result.startswith("data:image/")
            assert "base64," in result
            
            print(f"\nStyle '{style}' - Image data URI length: {len(result)}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not HAS_OPENAI_KEY,
        reason="OpenAI API key required"
    )
    async def test_openai_image_generator_direct(self):
        """Test OpenAI image generator directly"""
        from app.services.ai_services.image_generator import OpenAIImageGenerator
        
        generator = OpenAIImageGenerator()
        
        prompt = "a cute rabbit in a garden, children's book illustration"
        
        result = await generator.generate(prompt, style="cartoon")
        
        assert isinstance(result, str)
        assert result.startswith("data:image/")
        assert "base64," in result
        
        print(f"\nOpenAI image result length: {len(result)}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not (HAS_STABILITY_KEY and HAS_OPENAI_KEY),
        reason="Stability API key and OpenAI API key required"
    )
    async def test_image_generator_fallback_mechanism(self):
        """Test fallback mechanism for image generation"""
        generator = get_image_generator()
        
        prompt = "a magical unicorn in a rainbow forest"
        
        result = await generator.generate(prompt)
        
        # Should get a result from either primary or fallback
        assert isinstance(result, str)
        assert result.startswith("data:image/")
        print(f"\nImage result (from primary or fallback): {result[:100]}...")


@pytest.mark.integration
class TestEndToEndStoryGeneration:
    """End-to-end test for story generation workflow"""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not (HAS_AWS_CREDENTIALS and HAS_OPENAI_KEY and HAS_STABILITY_KEY),
        reason="All API keys required for end-to-end test"
    )
    async def test_story_generation_workflow(self):
        """Test complete story generation workflow"""
        text_generator = get_text_generator()
        image_generator = get_image_generator()
        
        # Step 1: Generate story text
        story_prompt = """Write a children's story chapter (3-4 sentences) about a rabbit 
        discovering a hidden treasure in the forest. Make it engaging and age-appropriate."""
        
        story_text = await text_generator.generate(
            story_prompt,
            temperature=0.8,
            max_tokens=200
        )
        
        assert isinstance(story_text, str)
        assert len(story_text) > 50
        
        # Step 2: Generate image prompt from story
        image_prompt_text = f"""Based on this story: "{story_text[:100]}..."
        Create a detailed image prompt for a children's book illustration."""
        
        image_prompt = await text_generator.generate(
            image_prompt_text,
            temperature=0.7,
            max_tokens=100
        )
        
        assert isinstance(image_prompt, str)
        assert len(image_prompt) > 20
        
        # Step 3: Generate image
        image_data = await image_generator.generate(
            image_prompt,
            style="children's book illustration"
        )
        
        assert isinstance(image_data, str)
        assert image_data.startswith("data:image/")
        
        print(f"\n=== Story Generation Workflow Test ===")
        print(f"Story text: {story_text}")
        print(f"Image prompt: {image_prompt}")
        print(f"Image generated: {len(image_data)} characters")
        print("=" * 50)

