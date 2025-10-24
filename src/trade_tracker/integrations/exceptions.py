"""Custom exceptions for broker integrations."""


class BrokerIntegrationError(Exception):
    """Base exception for broker integration errors."""
    pass


class BrokerConnectionError(BrokerIntegrationError):
    """Raised when broker connection fails."""
    pass


class BrokerAuthenticationError(BrokerIntegrationError):
    """Raised when broker authentication fails."""
    pass


class BrokerDataError(BrokerIntegrationError):
    """Raised when broker data is invalid or cannot be parsed."""
    pass


class CredentialError(BrokerIntegrationError):
    """Raised when credential operations fail."""
    pass


class DuplicateTradeError(BrokerIntegrationError):
    """Raised when attempting to import duplicate trades."""
    pass
