from datetime import datetime
from ..logging_config import logger

class AuditLogger:
    @staticmethod
    def log_security_event(
        event_type: str,
        user: str = None,
        success: bool = True,
        **kwargs
    ):
        """Log security-related events with redaction of sensitive data."""
        # Redact sensitive information
        redacted_kwargs = {
            k: "[REDACTED]" if any(s in k.lower() for s in ["key", "token", "secret", "password"]) 
            else v for k, v in kwargs.items()
        }
        
        logger.info(
            "Security Event",
            extra={
                "event_type": event_type,
                "user": user,
                "success": success,
                "timestamp": datetime.utcnow().isoformat(),
                **redacted_kwargs
            }
        )
