import json

from miner_base import StatusUpdater, TSK_STATUS, LOG_LEVEL


class LoggerStatusUpdater(StatusUpdater):
    """用于Test"""

    def update(self, status: TSK_STATUS | None, level: LOG_LEVEL, msg: str, extra: dict, error: Exception = None):
        log_msg = json.dumps({'status': status, 'msg': msg, 'extra': extra, 'error': str(error)},ensure_ascii=False)
        if self.logger is print:
            print(log_msg)
            return
        if level == 'DEBUG':
            self.logger.debug(log_msg)
        elif level == 'INFO':
            self.logger.info(log_msg)
        elif level == 'SUCCESS':
            self.logger.success(log_msg)
        elif level == 'WARNING':
            self.logger.warning(log_msg)
        elif level == 'ERROR':
            self.logger.error(log_msg)
        elif level == 'CRITICAL':
            self.logger.critical(log_msg)
        pass

    def __init__(self, logger):
        """可以传入 print ,直接打印到cli"""
        self.logger = logger
