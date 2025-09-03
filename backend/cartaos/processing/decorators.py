import time
import functools
from typing import Callable, Any, Dict
from ..logging_config import logger

def log_processing_stage(stage_name: str):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            file_path = kwargs.get('file_path', 'unknown')
            logger.info(
                f"Starting {stage_name}",
                extra={
                    "stage": stage_name,
                    "file_path": file_path,
                    "status": "started"
                }
            )
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                process_time = time.time() - start_time
                
                logger.info(
                    f"Completed {stage_name}",
                    extra={
                        "stage": stage_name,
                        "file_path": file_path,
                        "status": "completed",
                        "process_time_seconds": round(process_time, 4)
                    }
                )
                return result
                
            except Exception as e:
                process_time = time.time() - start_time
                logger.error(
                    f"Failed {stage_name}",
                    extra={
                        "stage": stage_name,
                        "file_path": file_path,
                        "status": "failed",
                        "error": str(e),
                        "error_type": e.__class__.__name__,
                        "process_time_seconds": round(process_time, 4)
                    },
                    exc_info=True
                )
                raise
        return wrapper
    return decorator
