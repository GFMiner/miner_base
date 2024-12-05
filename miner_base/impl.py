import json
from typing import Any

import loguru

from miner_base import StatusUpdater, TSK_STATUS, LOG_LEVEL, ON_LOG


class LoggerStatusUpdater(StatusUpdater):
    """用于Test"""
    on_log: ON_LOG

    def update(self, status: TSK_STATUS | None, level: LOG_LEVEL, msg: str, extra: dict, error: Exception = None):
        self.on_log(status, level, msg, extra, error)
        pass

    @classmethod
    def of(cls, on_log: ON_LOG):
        return cls(logger=on_log, compatible=False)

    @classmethod
    def of_logger(cls, lg: loguru.Logger):
        return cls(logger=lg, compatible=True)

    @staticmethod
    def _on_log_compatible(logger: loguru.Logger | None) -> ON_LOG:
        """用于兼容早期构造"""
        if logger is None:
            logger = loguru.logger
        if logger is print:
            logger = print

        def on_log(status: TSK_STATUS | None, level: LOG_LEVEL, msg: str, extra: dict, error: Exception = None):
            _m = json.dumps({'status': status, 'msg': msg, 'extra': extra, 'error': str(error)}, ensure_ascii=False)
            if level == 'DEBUG':
                logger.debug(_m)
            elif level == 'INFO':
                logger.info(_m)
            elif level == 'SUCCESS':
                logger.success(_m)
            elif level == 'WARNING':
                logger.warning(_m)
            elif level == 'ERROR':
                logger.error(_m)
            elif level == 'CRITICAL':
                logger.critical(_m)

        return on_log
        pass

    def __init__(self, logger: ON_LOG | Any, compatible=True):
        """可以传入 print ,直接打印到cli"""
        if compatible:
            self.on_log = self._on_log_compatible(logger)
        else:
            self.on_log = logger
