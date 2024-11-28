from abc import ABC
from typing import Literal


class ExecutorException(ABC, Exception):
    """交互器内部错误, 用于task mgr管理异常
    """
    err_name: str
    msg: str
    extra: dict

    def __init__(self, err_name: str, msg: str, extra: dict):
        self.err_name = err_name
        self.msg = msg
        self.extra = extra

    def __str__(self):
        return f'<{self.__class__.__name__}> {self.err_name}: {self.msg}'


class FatalExecutorException(ExecutorException):
    """抛出此类型异常后,仅由retry重试, 仍然失败则结束任务; 一般用于不可自动恢复的错误
    其他类型错误则通过asyncio.sleep后重新尝试
    """


class InteractorArgsException(FatalExecutorException):
    """本异常代表交互器参数不可用, 参数错误..."""

    def __init__(self, msg: str = '', args: dict = None):
        super().__init__('InteractorArgsException', msg, {'error_args': args or {}})


class SessionException(FatalExecutorException):
    """本异常代表session不可用"""

    def __init__(self, session_name: str, err_name: str = 'SessionException', msg: str = ''):
        super().__init__(err_name, msg, {'session_name': session_name})

    @property
    def session_name(self):
        return self.extra.get('session_name')


class ProxyException(FatalExecutorException):
    """本异常代表proxy不可用"""

    def __init__(self, proxy_snap: str, err_name: str = 'ProxyException', msg: str = ''):
        super().__init__(err_name, msg, {'proxy_snap': proxy_snap})

    @property
    def proxy_snap(self):  # 可能是 snap的 list, (proxy chain)
        return self.extra.get('proxy_snap')


# ====
class NormalExecutorException(ExecutorException):
    """代表出现该异常时可以尝试重试"""
    pass


class NetworkException(NormalExecutorException):
    """本异常代表网络不可用"""

    def __init__(self, msg: str, err_name: Literal['PROXY_TIMEOUT', 'PROXY_ERROR', 'NET_TIMEOUT'] = 'PROXY_TIMEOUT'):
        super().__init__(msg, err_name, {})

    pass
