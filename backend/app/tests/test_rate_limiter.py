"""
Unit tests for Rate Limiter (Task #30)

Tests rate limiting functionality for Claude API calls.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch

from app.services.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    RateLimitExceeded,
    RateLimitStatus,
    SlidingWindowCounter,
    LimitType,
    get_rate_limiter,
    configure_rate_limiter,
)


class TestSlidingWindowCounter:
    """Tests for SlidingWindowCounter."""
    
    def test_basic_acquire(self):
        """Test basic acquire functionality."""
        counter = SlidingWindowCounter(limit=5, window_seconds=60.0)
        
        # Should succeed for first 5 requests
        for i in range(5):
            assert counter.try_acquire(1) is True
        
        # 6th request should fail
        assert counter.try_acquire(1) is False
    
    def test_get_remaining(self):
        """Test remaining capacity calculation."""
        counter = SlidingWindowCounter(limit=10, window_seconds=60.0)
        
        assert counter.get_remaining() == 10
        
        counter.try_acquire(3)
        assert counter.get_remaining() == 7
        
        counter.try_acquire(5)
        assert counter.get_remaining() == 2
    
    def test_window_expiry(self):
        """Test that old entries expire."""
        counter = SlidingWindowCounter(limit=2, window_seconds=0.1)  # 100ms window
        
        counter.try_acquire(1)
        counter.try_acquire(1)
        assert counter.try_acquire(1) is False  # Limit reached
        
        # Wait for window to expire
        time.sleep(0.15)
        
        # Should be able to acquire again
        assert counter.try_acquire(1) is True
    
    def test_reset(self):
        """Test counter reset."""
        counter = SlidingWindowCounter(limit=5, window_seconds=60.0)
        
        counter.try_acquire(5)
        assert counter.get_remaining() == 0
        
        counter.reset()
        assert counter.get_remaining() == 5
    
    def test_token_counting(self):
        """Test counting with variable amounts (for tokens)."""
        counter = SlidingWindowCounter(limit=1000, window_seconds=60.0)
        
        assert counter.try_acquire(500) is True
        assert counter.get_remaining() == 500
        
        assert counter.try_acquire(300) is True
        assert counter.get_remaining() == 200
        
        # This should fail - not enough capacity
        assert counter.try_acquire(300) is False


class TestRateLimiter:
    """Tests for RateLimiter."""
    
    @pytest.fixture
    def limiter(self):
        """Create rate limiter with test config."""
        config = RateLimitConfig(
            requests_per_minute=10,
            tokens_per_minute=10000,
            per_user_rpm=5,
            per_user_tpm=5000,
            queue_timeout=1.0,
        )
        return RateLimiter(config)
    
    def test_check_rate_limit(self, limiter):
        """Test checking rate limit status."""
        status = limiter.check_rate_limit("user-1")
        
        assert status.requests_remaining > 0
        assert status.tokens_remaining > 0
        assert status.is_limited is False
    
    def test_acquire_success(self, limiter):
        """Test successful acquire."""
        result = limiter.acquire("user-1", estimated_tokens=100, wait=False)
        assert result is True
        
        status = limiter.check_rate_limit("user-1")
        assert status.requests_remaining == 4  # per_user_rpm - 1
    
    def test_acquire_exceeds_rpm(self, limiter):
        """Test acquire when RPM limit exceeded."""
        # Exhaust per-user RPM limit
        for _ in range(5):
            limiter.acquire("user-1", estimated_tokens=100, wait=False)
        
        # Next request should fail
        with pytest.raises(RateLimitExceeded) as exc_info:
            limiter.acquire("user-1", estimated_tokens=100, wait=False)
        
        assert exc_info.value.retry_after > 0
    
    def test_acquire_exceeds_tpm(self, limiter):
        """Test acquire when TPM limit exceeded."""
        # Use up most of the token budget
        limiter.acquire("user-1", estimated_tokens=4500, wait=False)
        
        # This should fail - not enough tokens
        with pytest.raises(RateLimitExceeded):
            limiter.acquire("user-1", estimated_tokens=1000, wait=False)
    
    def test_per_user_isolation(self, limiter):
        """Test that per-user limits are isolated."""
        # Exhaust user-1's limit
        for _ in range(5):
            limiter.acquire("user-1", estimated_tokens=100, wait=False)
        
        # user-2 should still be able to make requests
        result = limiter.acquire("user-2", estimated_tokens=100, wait=False)
        assert result is True
    
    def test_global_limit(self, limiter):
        """Test global rate limit."""
        # Make requests from multiple users to hit global limit
        for i in range(10):
            limiter.acquire(f"user-{i}", estimated_tokens=100, wait=False)
        
        # Global limit should be reached
        with pytest.raises(RateLimitExceeded):
            limiter.acquire("user-new", estimated_tokens=100, wait=False)
    
    def test_get_stats(self, limiter):
        """Test getting rate limiter stats."""
        limiter.acquire("user-1", estimated_tokens=100, wait=False)
        
        stats = limiter.get_stats()
        
        assert "global_rpm_remaining" in stats
        assert "global_tpm_remaining" in stats
        assert "config" in stats
        assert stats["config"]["requests_per_minute"] == 10
    
    def test_reset_user(self, limiter):
        """Test resetting specific user's limits."""
        # Exhaust user-1's limit
        for _ in range(5):
            limiter.acquire("user-1", estimated_tokens=100, wait=False)
        
        # Reset user-1
        limiter.reset("user-1")
        
        # user-1 should be able to make requests again
        result = limiter.acquire("user-1", estimated_tokens=100, wait=False)
        assert result is True
    
    def test_reset_all(self, limiter):
        """Test resetting all limits."""
        # Make some requests
        for _ in range(5):
            limiter.acquire("user-1", estimated_tokens=100, wait=False)
        
        # Reset all
        limiter.reset()
        
        stats = limiter.get_stats()
        assert stats["global_rpm_remaining"] == 10


class TestRateLimitStatus:
    """Tests for RateLimitStatus."""
    
    def test_to_dict(self):
        """Test status to dict conversion."""
        status = RateLimitStatus(
            requests_remaining=10,
            tokens_remaining=5000,
            reset_at=1733300000.0,
            is_limited=False,
            retry_after=0.0,
        )
        
        result = status.to_dict()
        
        assert result["requests_remaining"] == 10
        assert result["tokens_remaining"] == 5000
        assert result["is_limited"] is False


class TestRateLimitConfig:
    """Tests for RateLimitConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = RateLimitConfig()
        
        assert config.requests_per_minute == 60
        assert config.tokens_per_minute == 100000
        assert config.per_user_rpm == 20
        assert config.per_user_tpm == 50000
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = RateLimitConfig(
            requests_per_minute=30,
            tokens_per_minute=50000,
            per_user_rpm=10,
        )
        
        assert config.requests_per_minute == 30
        assert config.tokens_per_minute == 50000
        assert config.per_user_rpm == 10


class TestGlobalRateLimiter:
    """Tests for global rate limiter functions."""
    
    def test_get_rate_limiter(self):
        """Test getting global rate limiter."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        
        # Should return same instance
        assert limiter1 is limiter2
    
    def test_configure_rate_limiter(self):
        """Test configuring rate limiter."""
        config = RateLimitConfig(requests_per_minute=100)
        limiter = configure_rate_limiter(config)
        
        assert limiter.config.requests_per_minute == 100


class TestRateLimitExceeded:
    """Tests for RateLimitExceeded exception."""
    
    def test_exception_message(self):
        """Test exception message."""
        exc = RateLimitExceeded("Test message", retry_after=30.0)
        
        assert str(exc) == "Test message"
        assert exc.retry_after == 30.0
    
    def test_default_retry_after(self):
        """Test default retry_after value."""
        exc = RateLimitExceeded("Test")
        
        assert exc.retry_after == 60.0


class TestThreadSafety:
    """Tests for thread safety."""
    
    def test_concurrent_acquire(self):
        """Test concurrent acquire operations."""
        config = RateLimitConfig(
            requests_per_minute=100,
            per_user_rpm=100,
        )
        limiter = RateLimiter(config)
        
        results = []
        errors = []
        
        def make_request():
            try:
                result = limiter.acquire("user-1", estimated_tokens=10, wait=False)
                results.append(result)
            except RateLimitExceeded:
                errors.append(1)
        
        # Create 50 threads making concurrent requests
        threads = [threading.Thread(target=make_request) for _ in range(50)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All should succeed (under limit)
        assert len(results) == 50
        assert len(errors) == 0
    
    def test_concurrent_exceed_limit(self):
        """Test concurrent requests exceeding limit."""
        config = RateLimitConfig(
            requests_per_minute=10,
            per_user_rpm=10,
        )
        limiter = RateLimiter(config)
        
        results = []
        errors = []
        
        def make_request():
            try:
                result = limiter.acquire("user-1", estimated_tokens=10, wait=False)
                results.append(result)
            except RateLimitExceeded:
                errors.append(1)
        
        # Create 20 threads (more than limit)
        threads = [threading.Thread(target=make_request) for _ in range(20)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Some should succeed, some should fail
        assert len(results) <= 10
        assert len(errors) >= 10
        assert len(results) + len(errors) == 20
