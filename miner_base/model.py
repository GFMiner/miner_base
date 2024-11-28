from abc import ABC, abstractmethod
from typing import Literal, TypedDict, Optional

LOG_LEVEL = Literal['TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL']

TSK_STATUS = Literal['initialized', 'queued', 'running', 'completed', 'canceled', 'failed']


class CallAPIArgs(TypedDict, total=False):
    """call_api的入参"""
    api_name: str
    url: Optional[str]
    headers: Optional[dict]  # 替换
    params: Optional[dict]
    data: Optional[dict]
    update_headers: Optional[dict]  # 更新
    update_params: Optional[dict]


class StatusUpdater(ABC):
    """状态更新器, 替换交互器中的logger"""

    @abstractmethod
    def update(self, status: TSK_STATUS | None, level: LOG_LEVEL, msg: str, extra: dict, error: Exception = None):
        pass

    def debug(self, msg: str, level: LOG_LEVEL = 'INFO', status: TSK_STATUS = None, extra: dict = None):
        return self.update(status=status, level=level, msg=msg, extra=extra)

    def info(self, msg: str, level: LOG_LEVEL = 'INFO', status: TSK_STATUS = None, extra: dict = None):
        return self.update(status=status, level=level, msg=msg, extra=extra)

    def success(self, msg: str, level: LOG_LEVEL = 'SUCCESS', status: TSK_STATUS = None, extra: dict = None):
        return self.update(status=status, level=level, msg=msg, extra=extra)

    def warning(self, msg: str, level: LOG_LEVEL = 'WARNING', status: TSK_STATUS = None, extra: dict = None,
                error: Exception = None):
        return self.update(status=status, level=level, msg=msg, extra=extra, error=error)

    def error(self, msg: str, level: LOG_LEVEL = 'ERROR', status: TSK_STATUS = None, extra: dict = None,
              error: Exception = None):
        return self.update(status=status, level=level, msg=msg, extra=extra, error=error)

    def critical(self, msg: str, level: LOG_LEVEL = 'CRITICAL', status: TSK_STATUS = None, extra: dict = None,
                 error: Exception = None):
        return self.update(status=status, level=level, msg=msg, extra=extra, error=error)
