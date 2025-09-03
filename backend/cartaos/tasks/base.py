import time
from typing import Callable, Any
from ..logging_config import logger

class TaskMonitor:
    @classmethod
    def monitor_task(cls, task_name: str):
        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                task_id = kwargs.get('task_id', 'unknown')
                logger.info(
                    f"Starting task {task_name}",
                    extra={
                        "task_name": task_name,
                        "task_id": task_id,
                        "status": "started"
                    }
                )
                
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    process_time = time.time() - start_time
                    
                    logger.info(
                        f"Completed task {task_name}",
                        extra={
                            "task_name": task_name,
                            "task_id": task_id,
                            "status": "completed",
                            "process_time_seconds": round(process_time, 4)
                        }
                    )
                    return result
                    
                except Exception as e:
                    process_time = time.time() - start_time
                    logger.error(
                        f"Failed task {task_name}",
                        extra={
                            "task_name": task_name,
                            "task_id": task_id,
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
