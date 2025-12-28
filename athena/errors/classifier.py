"""Error classification for intelligent recovery."""

from enum import Enum
from typing import Optional
import re


class ErrorType(Enum):
    """Categories of errors for recovery strategies."""

    NETWORK = "network"  # Connection issues, timeouts, API errors
    FILE_NOT_FOUND = "file_not_found"  # Missing files or directories
    PERMISSION = "permission"  # Access denied, permission errors
    SYNTAX = "syntax"  # Code syntax errors
    VALIDATION = "validation"  # Input validation errors
    RATE_LIMIT = "rate_limit"  # API rate limiting
    TIMEOUT = "timeout"  # Operation timeouts
    UNKNOWN = "unknown"  # Unclassified errors


class ErrorClassifier:
    """Classify errors to determine recovery strategy."""

    # Network error patterns
    NETWORK_PATTERNS = [
        r"connection.*error",
        r"network.*error",
        r"unable to connect",
        r"connection refused",
        r"connection reset",
        r"network is unreachable",
        r"name resolution failed",
        r"dns.*failed",
        r"could not resolve host",
        r"failed to establish connection",
        r"socket.*error",
        r"http.*error",
        r"ssl.*error",
        r"certificate.*error",
    ]

    # File not found patterns
    FILE_NOT_FOUND_PATTERNS = [
        r"no such file or directory",
        r"file not found",
        r"path not found",
        r"does not exist",
        r"cannot find.*file",
        r"cannot find.*path",
        r"\[Errno 2\]",
        r"FileNotFoundError",
    ]

    # Permission error patterns
    PERMISSION_PATTERNS = [
        r"permission denied",
        r"access denied",
        r"access is denied",
        r"operation not permitted",
        r"you don't have permission",
        r"insufficient permissions",
        r"\[Errno 13\]",
        r"PermissionError",
        r"forbidden",
        r"unauthorized",
        r"401.*unauthorized",
        r"403.*forbidden",
    ]

    # Syntax error patterns
    SYNTAX_PATTERNS = [
        r"syntax.*error",
        r"invalid syntax",
        r"SyntaxError",
        r"parse.*error",
        r"unexpected.*token",
        r"unexpected.*symbol",
        r"missing.*semicolon",
        r"unterminated.*string",
    ]

    # Validation error patterns
    VALIDATION_PATTERNS = [
        r"validation.*error",
        r"invalid.*input",
        r"invalid.*parameter",
        r"invalid.*argument",
        r"bad.*request",
        r"400.*bad request",
        r"ValueError",
        r"TypeError",
        r"missing.*required",
    ]

    # Rate limit patterns
    RATE_LIMIT_PATTERNS = [
        r"rate limit",
        r"too many requests",
        r"429.*too many",
        r"quota.*exceeded",
        r"throttled",
        r"request limit",
    ]

    # Timeout patterns
    TIMEOUT_PATTERNS = [
        r"timeout",
        r"timed out",
        r"time.*out",
        r"deadline exceeded",
        r"operation.*timeout",
        r"request.*timeout",
        r"TimeoutError",
    ]

    # Request size patterns (like 413 errors)
    REQUEST_SIZE_PATTERNS = [
        r"413.*request entity too large",
        r"request.*too large",
        r"payload.*too large",
        r"content.*too large",
    ]

    @classmethod
    def classify(cls, error_message: str, error_type: Optional[type] = None) -> ErrorType:
        """Classify an error based on its message and type.

        Args:
            error_message: Error message text
            error_type: Optional exception type

        Returns:
            ErrorType classification
        """
        if not error_message:
            return ErrorType.UNKNOWN

        error_lower = error_message.lower()

        # Check exception type first
        if error_type:
            type_name = error_type.__name__
            if "FileNotFoundError" in type_name or "OSError" in type_name:
                if cls._matches_patterns(error_lower, cls.FILE_NOT_FOUND_PATTERNS):
                    return ErrorType.FILE_NOT_FOUND
                if cls._matches_patterns(error_lower, cls.PERMISSION_PATTERNS):
                    return ErrorType.PERMISSION
            elif "PermissionError" in type_name:
                return ErrorType.PERMISSION
            elif "TimeoutError" in type_name or "Timeout" in type_name:
                return ErrorType.TIMEOUT
            elif "SyntaxError" in type_name:
                return ErrorType.SYNTAX
            elif "ValueError" in type_name or "TypeError" in type_name:
                return ErrorType.VALIDATION
            elif "ConnectionError" in type_name or "NetworkError" in type_name:
                return ErrorType.NETWORK

        # Check patterns in priority order
        if cls._matches_patterns(error_lower, cls.RATE_LIMIT_PATTERNS):
            return ErrorType.RATE_LIMIT

        if cls._matches_patterns(error_lower, cls.TIMEOUT_PATTERNS):
            return ErrorType.TIMEOUT

        if cls._matches_patterns(error_lower, cls.NETWORK_PATTERNS):
            return ErrorType.NETWORK

        if cls._matches_patterns(error_lower, cls.FILE_NOT_FOUND_PATTERNS):
            return ErrorType.FILE_NOT_FOUND

        if cls._matches_patterns(error_lower, cls.PERMISSION_PATTERNS):
            return ErrorType.PERMISSION

        if cls._matches_patterns(error_lower, cls.SYNTAX_PATTERNS):
            return ErrorType.SYNTAX

        if cls._matches_patterns(error_lower, cls.VALIDATION_PATTERNS):
            return ErrorType.VALIDATION

        if cls._matches_patterns(error_lower, cls.REQUEST_SIZE_PATTERNS):
            # Treat request size errors as validation errors
            return ErrorType.VALIDATION

        return ErrorType.UNKNOWN

    @classmethod
    def _matches_patterns(cls, text: str, patterns: list[str]) -> bool:
        """Check if text matches any of the given patterns.

        Args:
            text: Text to check
            patterns: List of regex patterns

        Returns:
            True if any pattern matches
        """
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    @classmethod
    def is_retryable(cls, error_type: ErrorType) -> bool:
        """Determine if an error type is retryable.

        Args:
            error_type: Type of error

        Returns:
            True if the error should be retried
        """
        retryable_types = {
            ErrorType.NETWORK,
            ErrorType.TIMEOUT,
            ErrorType.RATE_LIMIT,
        }
        return error_type in retryable_types

    @classmethod
    def get_recovery_hint(cls, error_type: ErrorType, error_message: str) -> Optional[str]:
        """Get a helpful recovery hint for the error.

        Args:
            error_type: Type of error
            error_message: Original error message

        Returns:
            Helpful hint for recovery, or None
        """
        hints = {
            ErrorType.FILE_NOT_FOUND: "The file or directory does not exist. Check the path and try again.",
            ErrorType.PERMISSION: "Permission denied. You may need elevated privileges or need to check file permissions.",
            ErrorType.NETWORK: "Network connection issue. Check your internet connection and try again.",
            ErrorType.TIMEOUT: "Operation timed out. The server may be slow or unresponsive.",
            ErrorType.RATE_LIMIT: "Rate limit exceeded. Waiting before retrying...",
            ErrorType.SYNTAX: "Syntax error in code. Review and fix the syntax.",
            ErrorType.VALIDATION: "Invalid input or parameters. Check the values and try again.",
        }

        return hints.get(error_type)
