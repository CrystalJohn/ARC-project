"""
Unit tests for Task #32: Error Handling & Retry Logic for Bedrock

Tests the bedrock_retry module including:
- Error classification
- Retry decorator
- Custom exceptions
- RetryableBedrockClient
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, BotoCoreError

from app.services.bedrock_retry import (
    BedrockErrorType,
    RetryConfig,
    BedrockError,
    BedrockThrottlingError,
    BedrockServiceError,
    BedrockModelError,
    BedrockValidationError,
    BedrockAccessError,
    BedrockTimeoutError,
    ERROR_MESSAGES,
    classify_error,
    create_bedrock_error,
    with_retry,
    RetryableBedrockClient,
    bedrock_retry,
)


class TestRetryConfig:
    """Tests for RetryConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_retries == 5
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = RetryConfig(
            max_retries=3,
            base_delay=0.5,
            max_delay=30.0,
            exponential_base=3.0,
            jitter=False,
        )
        assert config.max_retries == 3
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
    
    def test_get_delay_exponential(self):
        """Test exponential backoff calculation."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)
        
        assert config.get_delay(0) == 1.0   # 1 * 2^0 = 1
        assert config.get_delay(1) == 2.0   # 1 * 2^1 = 2
        assert config.get_delay(2) == 4.0   # 1 * 2^2 = 4
        assert config.get_delay(3) == 8.0   # 1 * 2^3 = 8
    
    def test_get_delay_max_cap(self):
        """Test delay is capped at max_delay."""
        config = RetryConfig(base_delay=1.0, max_delay=10.0, jitter=False)
        
        assert config.get_delay(10) == 10.0  # Would be 1024, capped at 10
    
    def test_get_delay_with_jitter(self):
        """Test jitter adds randomness."""
        config = RetryConfig(base_delay=1.0, jitter=True)
        
        delays = [config.get_delay(0) for _ in range(10)]
        # With jitter, delays should vary
        assert len(set(delays)) > 1


class TestBedrockErrors:
    """Tests for BedrockError classes."""
    
    def test_base_error(self):
        """Test BedrockError base class."""
        error = BedrockError(
            message="Test error",
            error_type=BedrockErrorType.UNKNOWN,
            error_code="TestCode",
            retryable=False,
        )
        
        assert str(error) == "Test error"
        assert error.error_type == BedrockErrorType.UNKNOWN
        assert error.error_code == "TestCode"
        assert error.retryable is False
    
    def test_throttling_error(self):
        """Test BedrockThrottlingError."""
        error = BedrockThrottlingError()
        
        assert error.error_type == BedrockErrorType.THROTTLING
        assert error.retryable is True
        assert "rate limit" in error.message.lower()
    
    def test_service_error(self):
        """Test BedrockServiceError."""
        error = BedrockServiceError()
        
        assert error.error_type == BedrockErrorType.SERVICE_UNAVAILABLE
        assert error.retryable is True
    
    def test_model_error(self):
        """Test BedrockModelError."""
        error = BedrockModelError()
        
        assert error.error_type == BedrockErrorType.MODEL_ERROR
        assert error.retryable is False
    
    def test_validation_error(self):
        """Test BedrockValidationError."""
        error = BedrockValidationError()
        
        assert error.error_type == BedrockErrorType.VALIDATION
        assert error.retryable is False
    
    def test_access_error(self):
        """Test BedrockAccessError."""
        error = BedrockAccessError()
        
        assert error.error_type == BedrockErrorType.ACCESS_DENIED
        assert error.retryable is False
    
    def test_timeout_error(self):
        """Test BedrockTimeoutError."""
        error = BedrockTimeoutError()
        
        assert error.error_type == BedrockErrorType.TIMEOUT
        assert error.retryable is True
    
    def test_error_to_dict(self):
        """Test error serialization."""
        error = BedrockThrottlingError(error_code="ThrottlingException")
        
        d = error.to_dict()
        assert d["error_type"] == "throttling"
        assert d["error_code"] == "ThrottlingException"
        assert d["retryable"] is True
    
    def test_user_message(self):
        """Test user-friendly messages."""
        error = BedrockThrottlingError()
        
        assert error.user_message == ERROR_MESSAGES[BedrockErrorType.THROTTLING]
        assert "busy" in error.user_message.lower()


class TestClassifyError:
    """Tests for error classification."""
    
    def test_classify_throttling(self):
        """Test throttling error classification."""
        error = ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            "InvokeModel"
        )
        
        error_type, retryable, code = classify_error(error)
        
        assert error_type == BedrockErrorType.THROTTLING
        assert retryable is True
        assert code == "ThrottlingException"
    
    def test_classify_service_unavailable(self):
        """Test service unavailable classification."""
        error = ClientError(
            {"Error": {"Code": "ServiceUnavailableException", "Message": "Service down"}},
            "InvokeModel"
        )
        
        error_type, retryable, code = classify_error(error)
        
        assert error_type == BedrockErrorType.SERVICE_UNAVAILABLE
        assert retryable is True
    
    def test_classify_validation(self):
        """Test validation error classification."""
        error = ClientError(
            {"Error": {"Code": "ValidationException", "Message": "Invalid input"}},
            "InvokeModel"
        )
        
        error_type, retryable, code = classify_error(error)
        
        assert error_type == BedrockErrorType.VALIDATION
        assert retryable is False
    
    def test_classify_access_denied(self):
        """Test access denied classification."""
        error = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "No access"}},
            "InvokeModel"
        )
        
        error_type, retryable, code = classify_error(error)
        
        assert error_type == BedrockErrorType.ACCESS_DENIED
        assert retryable is False
    
    def test_classify_timeout(self):
        """Test timeout classification."""
        error = ClientError(
            {"Error": {"Code": "ModelTimeoutException", "Message": "Timeout"}},
            "InvokeModel"
        )
        
        error_type, retryable, code = classify_error(error)
        
        assert error_type == BedrockErrorType.TIMEOUT
        assert retryable is True
    
    def test_classify_botocore_error(self):
        """Test BotoCoreError classification."""
        error = BotoCoreError()
        
        error_type, retryable, code = classify_error(error)
        
        assert error_type == BedrockErrorType.SERVICE_UNAVAILABLE
        assert retryable is True
    
    def test_classify_timeout_error(self):
        """Test Python TimeoutError classification."""
        error = TimeoutError("Connection timed out")
        
        error_type, retryable, code = classify_error(error)
        
        assert error_type == BedrockErrorType.TIMEOUT
        assert retryable is True


class TestCreateBedrockError:
    """Tests for create_bedrock_error function."""
    
    def test_create_throttling_error(self):
        """Test creating throttling error."""
        original = ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            "InvokeModel"
        )
        
        error = create_bedrock_error(original)
        
        assert isinstance(error, BedrockThrottlingError)
        assert error.original_error is original
    
    def test_create_validation_error(self):
        """Test creating validation error."""
        original = ClientError(
            {"Error": {"Code": "ValidationException", "Message": "Bad input"}},
            "InvokeModel"
        )
        
        error = create_bedrock_error(original)
        
        assert isinstance(error, BedrockValidationError)
    
    def test_create_unknown_error(self):
        """Test creating unknown error."""
        original = Exception("Something went wrong")
        
        error = create_bedrock_error(original)
        
        assert isinstance(error, BedrockError)
        assert error.error_type == BedrockErrorType.UNKNOWN


class TestWithRetryDecorator:
    """Tests for with_retry decorator."""
    
    def test_success_no_retry(self):
        """Test successful call without retry."""
        call_count = 0
        
        @with_retry(max_retries=3)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_func()
        
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_throttling(self):
        """Test retry on throttling error."""
        call_count = 0
        
        @with_retry(max_retries=3, base_delay=0.01)
        def throttled_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ClientError(
                    {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
                    "InvokeModel"
                )
            return "success"
        
        result = throttled_func()
        
        assert result == "success"
        assert call_count == 3
    
    def test_no_retry_on_validation(self):
        """Test no retry on validation error."""
        call_count = 0
        
        @with_retry(max_retries=3, base_delay=0.01)
        def validation_func():
            nonlocal call_count
            call_count += 1
            raise ClientError(
                {"Error": {"Code": "ValidationException", "Message": "Bad input"}},
                "InvokeModel"
            )
        
        with pytest.raises(BedrockValidationError):
            validation_func()
        
        assert call_count == 1  # No retry
    
    def test_max_retries_exceeded(self):
        """Test error raised after max retries."""
        call_count = 0
        
        @with_retry(max_retries=2, base_delay=0.01)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ClientError(
                {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
                "InvokeModel"
            )
        
        with pytest.raises(BedrockThrottlingError):
            always_fails()
        
        assert call_count == 3  # Initial + 2 retries
    
    def test_on_retry_callback(self):
        """Test on_retry callback is called."""
        retry_calls = []
        
        def on_retry(attempt, error, delay):
            retry_calls.append((attempt, type(error).__name__, delay))
        
        @with_retry(max_retries=2, base_delay=0.01, on_retry=on_retry)
        def fails_twice():
            if len(retry_calls) < 2:
                raise ClientError(
                    {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
                    "InvokeModel"
                )
            return "success"
        
        result = fails_twice()
        
        assert result == "success"
        assert len(retry_calls) == 2
        assert retry_calls[0][0] == 0  # First retry attempt
        assert retry_calls[1][0] == 1  # Second retry attempt


class TestRetryableBedrockClient:
    """Tests for RetryableBedrockClient."""
    
    def test_invoke_model_success(self):
        """Test successful invoke_model."""
        mock_client = Mock()
        mock_client.invoke_model.return_value = {"body": Mock(read=lambda: b'{"result": "ok"}')}
        
        client = RetryableBedrockClient(mock_client)
        result = client.invoke_model(modelId="test", body="{}")
        
        assert result == {"body": mock_client.invoke_model.return_value["body"]}
        mock_client.invoke_model.assert_called_once()
    
    def test_invoke_model_retry(self):
        """Test invoke_model with retry."""
        mock_client = Mock()
        mock_client.invoke_model.side_effect = [
            ClientError(
                {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
                "InvokeModel"
            ),
            {"body": Mock(read=lambda: b'{"result": "ok"}')}
        ]
        
        config = RetryConfig(max_retries=2, base_delay=0.01)
        client = RetryableBedrockClient(mock_client, retry_config=config)
        
        result = client.invoke_model(modelId="test", body="{}")
        
        assert mock_client.invoke_model.call_count == 2
    
    def test_invoke_model_stream_success(self):
        """Test successful streaming invoke."""
        mock_client = Mock()
        mock_client.invoke_model_with_response_stream.return_value = {"body": []}
        
        client = RetryableBedrockClient(mock_client)
        result = client.invoke_model_with_response_stream(modelId="test", body="{}")
        
        assert "body" in result
        mock_client.invoke_model_with_response_stream.assert_called_once()


class TestBedrockRetryConvenience:
    """Tests for bedrock_retry convenience function."""
    
    def test_bedrock_retry_decorator(self):
        """Test bedrock_retry creates working decorator."""
        call_count = 0
        
        @bedrock_retry(max_retries=2, base_delay=0.01, operation_name="Test")
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ClientError(
                    {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
                    "InvokeModel"
                )
            return "success"
        
        result = test_func()
        
        assert result == "success"
        assert call_count == 2


class TestErrorMessages:
    """Tests for user-friendly error messages."""
    
    def test_all_error_types_have_messages(self):
        """Test all error types have user messages."""
        for error_type in BedrockErrorType:
            assert error_type in ERROR_MESSAGES
            assert len(ERROR_MESSAGES[error_type]) > 0
    
    def test_messages_are_user_friendly(self):
        """Test messages don't contain technical jargon."""
        technical_terms = ["exception", "error code", "boto", "aws", "api"]
        
        for message in ERROR_MESSAGES.values():
            message_lower = message.lower()
            for term in technical_terms:
                assert term not in message_lower, f"Found '{term}' in message: {message}"
