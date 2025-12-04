"""
Unit tests for Budget Manager (Task #31)

Tests budget tracking and automatic model fallback.
"""

import pytest
import time
from unittest.mock import Mock, patch

from app.services.budget_manager import (
    BudgetManager,
    BudgetConfig,
    BudgetStatus,
    UsageRecord,
    ModelTier,
    get_budget_manager,
    configure_budget_manager,
)


class TestBudgetConfig:
    """Tests for BudgetConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = BudgetConfig()
        
        assert config.daily_budget_usd == 10.0
        assert config.monthly_budget_usd == 200.0
        assert config.sonnet_threshold_pct == 0.7
        assert config.per_user_daily_usd == 2.0
        assert config.fallback_enabled is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = BudgetConfig(
            daily_budget_usd=5.0,
            monthly_budget_usd=100.0,
            sonnet_threshold_pct=0.5,
        )
        
        assert config.daily_budget_usd == 5.0
        assert config.monthly_budget_usd == 100.0
        assert config.sonnet_threshold_pct == 0.5


class TestUsageRecord:
    """Tests for UsageRecord."""
    
    def test_to_dict(self):
        """Test usage record to dict conversion."""
        record = UsageRecord(
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.05,
            model="sonnet",
        )
        
        result = record.to_dict()
        
        assert result["input_tokens"] == 1000
        assert result["output_tokens"] == 500
        assert result["cost_usd"] == 0.05
        assert result["model"] == "sonnet"


class TestBudgetManager:
    """Tests for BudgetManager."""
    
    @pytest.fixture
    def manager(self):
        """Create budget manager with test config."""
        config = BudgetConfig(
            daily_budget_usd=10.0,
            monthly_budget_usd=100.0,
            sonnet_threshold_pct=0.7,
            per_user_daily_usd=2.0,
        )
        return BudgetManager(config)
    
    def test_calculate_cost_sonnet(self, manager):
        """Test cost calculation for Sonnet."""
        # Sonnet: $3/1M input, $15/1M output
        cost = manager.calculate_cost(
            input_tokens=1_000_000,
            output_tokens=100_000,
            model="sonnet"
        )
        
        # $3 input + $1.5 output = $4.5
        assert cost == pytest.approx(4.5, rel=0.01)
    
    def test_calculate_cost_haiku(self, manager):
        """Test cost calculation for Haiku."""
        # Haiku: $0.25/1M input, $1.25/1M output
        cost = manager.calculate_cost(
            input_tokens=1_000_000,
            output_tokens=100_000,
            model="haiku"
        )
        
        # $0.25 input + $0.125 output = $0.375
        assert cost == pytest.approx(0.375, rel=0.01)
    
    def test_record_usage(self, manager):
        """Test recording usage."""
        record = manager.record_usage(
            input_tokens=10000,
            output_tokens=5000,
            model="sonnet",
            user_id="user-1"
        )
        
        assert record.input_tokens == 10000
        assert record.output_tokens == 5000
        assert record.cost_usd > 0
        assert record.model == "sonnet"
    
    def test_get_status_initial(self, manager):
        """Test initial budget status."""
        status = manager.get_status("user-1")
        
        assert status.daily_spent_usd == 0.0
        assert status.monthly_spent_usd == 0.0
        assert status.daily_remaining_usd == 10.0
        assert status.is_over_budget is False
        assert status.fallback_active is False
        assert status.recommended_model == ModelTier.SONNET
    
    def test_get_status_after_usage(self, manager):
        """Test budget status after recording usage."""
        # Record some usage
        manager.record_usage(1_000_000, 500_000, "sonnet", "user-1")
        
        status = manager.get_status("user-1")
        
        assert status.daily_spent_usd > 0
        assert status.daily_remaining_usd < 10.0
    
    def test_fallback_triggered(self, manager):
        """Test that fallback is triggered when threshold reached."""
        # Record enough usage to trigger fallback (>70% of $10 = $7)
        # Need about 2.3M input tokens at $3/1M = $7
        manager.record_usage(2_500_000, 0, "sonnet", "user-1")
        
        status = manager.get_status("user-1")
        
        assert status.fallback_active is True
        assert status.recommended_model == ModelTier.HAIKU
    
    def test_get_recommended_model_under_threshold(self, manager):
        """Test recommended model when under threshold."""
        model = manager.get_recommended_model("user-1")
        assert model == ModelTier.SONNET
    
    def test_get_recommended_model_over_threshold(self, manager):
        """Test recommended model when over threshold."""
        # Trigger fallback
        manager.record_usage(2_500_000, 0, "sonnet", "user-1")
        
        model = manager.get_recommended_model("user-1")
        assert model == ModelTier.HAIKU
    
    def test_check_user_budget(self, manager):
        """Test per-user budget check."""
        assert manager.check_user_budget("user-1") is True
        
        # Exceed user budget ($2)
        manager.record_usage(1_000_000, 0, "sonnet", "user-1")  # $3
        
        assert manager.check_user_budget("user-1") is False
    
    def test_get_user_spending(self, manager):
        """Test getting user spending summary."""
        manager.record_usage(100_000, 50_000, "sonnet", "user-1")
        
        spending = manager.get_user_spending("user-1")
        
        assert "daily_spent_usd" in spending
        assert "monthly_spent_usd" in spending
        assert "daily_limit_usd" in spending
        assert spending["daily_limit_usd"] == 2.0
    
    def test_estimate_request_cost(self, manager):
        """Test request cost estimation."""
        estimate = manager.estimate_request_cost(
            estimated_input_tokens=10000,
            estimated_output_tokens=2000,
        )
        
        assert "sonnet_cost_usd" in estimate
        assert "haiku_cost_usd" in estimate
        assert "savings_with_haiku_usd" in estimate
        assert estimate["sonnet_cost_usd"] > estimate["haiku_cost_usd"]
    
    def test_get_stats(self, manager):
        """Test getting overall statistics."""
        manager.record_usage(100_000, 50_000, "sonnet", "user-1")
        
        stats = manager.get_stats()
        
        assert "daily" in stats
        assert "monthly" in stats
        assert "config" in stats
        assert stats["daily"]["spent_usd"] > 0
    
    def test_reset_daily(self, manager):
        """Test resetting daily counters."""
        manager.record_usage(100_000, 50_000, "sonnet", "user-1")
        
        manager.reset(daily=True, monthly=False)
        
        stats = manager.get_stats()
        assert stats["daily"]["spent_usd"] == 0
        assert stats["monthly"]["spent_usd"] > 0  # Monthly not reset
    
    def test_reset_all(self, manager):
        """Test resetting all counters."""
        manager.record_usage(100_000, 50_000, "sonnet", "user-1")
        
        manager.reset(daily=True, monthly=True)
        
        stats = manager.get_stats()
        assert stats["daily"]["spent_usd"] == 0
        assert stats["monthly"]["spent_usd"] == 0
    
    def test_per_user_isolation(self, manager):
        """Test that per-user tracking is isolated."""
        manager.record_usage(100_000, 0, "sonnet", "user-1")
        manager.record_usage(200_000, 0, "sonnet", "user-2")
        
        user1_spending = manager.get_user_spending("user-1")
        user2_spending = manager.get_user_spending("user-2")
        
        assert user1_spending["daily_spent_usd"] < user2_spending["daily_spent_usd"]


class TestBudgetStatus:
    """Tests for BudgetStatus."""
    
    def test_to_dict(self):
        """Test status to dict conversion."""
        status = BudgetStatus(
            daily_spent_usd=5.0,
            monthly_spent_usd=50.0,
            daily_remaining_usd=5.0,
            monthly_remaining_usd=150.0,
            daily_budget_pct=50.0,
            monthly_budget_pct=25.0,
            recommended_model=ModelTier.SONNET,
            is_over_budget=False,
            fallback_active=False,
        )
        
        result = status.to_dict()
        
        assert result["daily_spent_usd"] == 5.0
        assert result["recommended_model"] == "sonnet"
        assert result["is_over_budget"] is False


class TestGlobalBudgetManager:
    """Tests for global budget manager functions."""
    
    def test_get_budget_manager(self):
        """Test getting global budget manager."""
        manager1 = get_budget_manager()
        manager2 = get_budget_manager()
        
        # Should return same instance
        assert manager1 is manager2
    
    def test_configure_budget_manager(self):
        """Test configuring budget manager."""
        config = BudgetConfig(daily_budget_usd=20.0)
        manager = configure_budget_manager(config)
        
        assert manager.config.daily_budget_usd == 20.0


class TestFallbackDisabled:
    """Tests for fallback disabled scenario."""
    
    def test_no_fallback_when_disabled(self):
        """Test that fallback doesn't trigger when disabled."""
        config = BudgetConfig(
            daily_budget_usd=10.0,
            sonnet_threshold_pct=0.7,
            fallback_enabled=False,
        )
        manager = BudgetManager(config)
        
        # Exceed threshold
        manager.record_usage(2_500_000, 0, "sonnet", "user-1")
        
        status = manager.get_status("user-1")
        
        # Fallback should not be active
        assert status.fallback_active is False
        assert status.recommended_model == ModelTier.SONNET
