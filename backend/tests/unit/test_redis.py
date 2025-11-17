"""
Unit tests for Redis connection management
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.redis import RedisClient, get_redis


class TestRedisClient:
    """Test RedisClient class"""

    def test_redis_client_initialization(self):
        """Test RedisClient initialization"""
        client = RedisClient()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_redis_connect(self):
        """Test Redis connection"""
        client = RedisClient()
        
        with patch('app.core.redis.aioredis.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            await client.connect()
            
            assert client._client is not None
            mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_connect_idempotent(self):
        """Test that connect can be called multiple times safely"""
        client = RedisClient()
        
        with patch('app.core.redis.aioredis.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            await client.connect()
            await client.connect()  # Call again
            
            # Should only create connection once
            assert mock_from_url.call_count == 1

    @pytest.mark.asyncio
    async def test_redis_disconnect(self):
        """Test Redis disconnection"""
        client = RedisClient()
        
        with patch('app.core.redis.aioredis.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock()
            mock_redis.close = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            await client.connect()
            await client.disconnect()
            
            mock_redis.close.assert_called_once()
            assert client._client is None

    @pytest.mark.asyncio
    async def test_redis_client_property(self):
        """Test client property access"""
        client = RedisClient()
        
        with patch('app.core.redis.aioredis.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            await client.connect()
            
            # Should return the client
            assert client.client is mock_redis

    @pytest.mark.asyncio
    async def test_redis_client_property_not_connected(self):
        """Test client property raises error when not connected"""
        client = RedisClient()
        
        with pytest.raises(RuntimeError, match="Redis client not initialized"):
            _ = client.client


class TestGetRedis:
    """Test get_redis singleton function"""

    def test_get_redis_singleton(self):
        """Test that get_redis returns singleton"""
        # Clear cache to test fresh
        get_redis.cache_clear()
        
        client1 = get_redis()
        client2 = get_redis()
        
        assert client1 is client2

