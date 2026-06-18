class CalendarAPIError(Exception):
    """General exception for Google Calendar API errors."""
    def __init__(self, message, original_error=None):
        super().__init__(message)
        self.original_error = original_error

class AuthTokenExpiredError(CalendarAPIError):
    """Exception raised when the Google Calendar API authentication token is expired or invalid."""
    pass

class ApiQuotaExceededError(CalendarAPIError):
    """Exception raised when the Google Calendar API quota is exceeded."""
    pass

class CalendarEventNotFoundError(CalendarAPIError):
    """Exception raised when a specific calendar event is not found."""
    pass

class CalendarEventConflictError(CalendarAPIError):
    """Exception raised when multiple events match the criteria for a single operation."""
    pass

class AuthRequiredError(CalendarAPIError):
    """Exception raised when user authentication is required."""
    pass