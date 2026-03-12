class DesignLabError(Exception):
    """Base exception for Design Lab failures."""
    pass


class MermaidValidationLimitExceeded(DesignLabError):
    """Raised when the Architect fails to produce valid
    Mermaid syntax after several retries."""
    pass
