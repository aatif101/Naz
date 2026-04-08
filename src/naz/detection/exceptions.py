class NazDetectionError(Exception):
    """Base class for all detection-layer errors."""


class NodeNotFoundError(NazDetectionError):
    """Raised when npx is not found on PATH (Node.js not installed)."""


class SpecfyTimeoutError(NazDetectionError):
    """Raised when Specfy subprocess exceeds the 120-second timeout."""


class SpecfyError(NazDetectionError):
    """Raised when Specfy returns a non-zero exit code or unparseable output."""

    def __init__(self, message: str, stderr: str = "") -> None:
        super().__init__(message)
        self.stderr = stderr
