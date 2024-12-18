import re
from abc import abstractmethod
from typing import TypedDict, Optional, Any, Union, Mapping, Callable, Awaitable, Iterable, Unpack, Generic

from aiohttp import ClientResponse, BasicAuth, Fingerprint, ClientTimeout
# noinspection PyProtectedMember
from aiohttp.client import SSLContext, ClientSession
from aiohttp.typedefs import LooseHeaders, StrOrURL, LooseCookies, Query
from pydantic import BaseModel, Field, PrivateAttr
from pydantic.dataclasses import dataclass
from typing_extensions import TypeVar

from miner_base.exception import *


class AgentInfo(TypedDict):
    """用户信息字段"""
    useragent: str
    percent: int
    type: str
    system: str
    browser: str
    version: int | str
    os: str


class TgSessionArgs(TypedDict):
    id: str | int
    session_name: str
    proxy_ip: str | None
    agent_info: AgentInfo


@dataclass
class State:
    """脚本状态管理器"""
    data: dict = Field(dict)

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def __call__(self, key: str, default=None):
        return self.get(key, default)

    def set(self, key: str, value: Any) -> Any:
        self.data[key] = value
        return value

    def clear(self):
        return self.data.clear()


class RequestOptions(TypedDict, total=False):
    params: Query
    data: Any
    json: Any
    cookies: Union[LooseCookies, None]
    headers: Union[LooseHeaders, None]
    skip_auto_headers: Union[Iterable[str], None]
    auth: Union[BasicAuth, None]
    allow_redirects: bool
    max_redirects: int
    compress: Union[str, bool, None]
    chunked: Union[bool, None]
    expect100: bool
    raise_for_status: Union[None, bool, Callable[[ClientResponse], Awaitable[None]]]
    read_until_eof: bool
    proxy: Union[StrOrURL, None]
    proxy_auth: Union[BasicAuth, None]
    timeout: Union[ClientTimeout, None]
    ssl: Union[SSLContext, bool, Fingerprint]
    server_hostname: Union[str, None]
    proxy_headers: Union[LooseHeaders, None]
    trace_request_ctx: Union[Mapping[str, Any], None]
    read_bufsize: Union[int, None]
    auto_decompress: Union[bool, None]
    max_line_size: Union[int, None]
    max_field_size: Union[int, None]


class APICaller(ABC):
    """API调用 或发送网络请求
    兼容 aiohttp"""

    @abstractmethod
    async def api(self, api_name: str,
                  url: Optional[StrOrURL] = None,  # 更新
                  headers: Optional[dict] = None,  # 替换
                  params: Optional[dict] = None,
                  data: Optional[dict] = None,
                  update_headers: Optional[dict] = None,  # 更新
                  update_params: Optional[dict] = None,
                  **kwargs: Unpack[RequestOptions],
                  ) -> str | dict:
        """调用API函数"""
        pass

    @property
    @abstractmethod
    def session(self) -> ClientSession:
        ...

    # noinspection PyUnresolvedReferences
    @abstractmethod
    def get(
            self,
            url: StrOrURL,
            **kwargs: Unpack[RequestOptions],
    ) -> "_RequestContextManager": ...

    # noinspection PyUnresolvedReferences
    @abstractmethod
    def options(
            self,
            url: StrOrURL,
            **kwargs: Unpack[RequestOptions],
    ) -> "_RequestContextManager": ...

    # noinspection PyUnresolvedReferences
    @abstractmethod
    def head(
            self,
            url: StrOrURL,
            **kwargs: Unpack[RequestOptions],
    ) -> "_RequestContextManager": ...

    # noinspection PyUnresolvedReferences
    @abstractmethod
    def post(
            self,
            url: StrOrURL,
            **kwargs: Unpack[RequestOptions],
    ) -> "_RequestContextManager": ...

    # noinspection PyUnresolvedReferences
    @abstractmethod
    def put(
            self,
            url: StrOrURL,
            **kwargs: Unpack[RequestOptions],
    ) -> "_RequestContextManager": ...

    # noinspection PyUnresolvedReferences
    @abstractmethod
    def patch(
            self,
            url: StrOrURL,
            **kwargs: Unpack[RequestOptions],
    ) -> "_RequestContextManager": ...

    # noinspection PyUnresolvedReferences
    @abstractmethod
    def delete(
            self,
            url: StrOrURL,
            **kwargs: Unpack[RequestOptions],
    ) -> "_RequestContextManager": ...


LOG_LEVEL = Literal['TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL']

TSK_STATUS = Literal['initialized', 'queued', 'running', 'completed', 'canceled', 'failed']

ON_LOG = Callable[[TSK_STATUS | None, LOG_LEVEL, str, dict, Exception | None], None]


class StatusUpdater(ABC):
    """状态更新器, 可替代logger, 用于将状态(日志等信息)共享给UI
    success以上级别(warning, error, ...)的日志将展示在 GUI-任务状态栏; 其他日志(info, debug...)需要进入日志管理查看
    """

    @abstractmethod
    def update(self, status: TSK_STATUS | None, level: LOG_LEVEL, msg: str, extra: dict, error: Exception = None):
        pass

    def debug(self, msg: str, level: LOG_LEVEL = 'DEBUG', status: TSK_STATUS = None, extra: dict = None):
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


TeleMobaiPlat = Literal['android', 'ios']


class GFMPlugin(ABC):

    @classmethod
    @abstractmethod
    def of_args(cls, args: 'ScriptRuntimeArgs', updater: StatusUpdater):
        """通过脚本args参数构造实例
        1种Class只能注册1个实例
        :returns plugin
        """
        plugin = [p for p in args.plugins() if isinstance(p, cls)]
        assert len(plugin) != 0, f'从args读取插件[{cls}]失败'
        return plugin[0]


class ScriptProfile(BaseModel, ABC):
    """脚本配置参数定义: 用户将在GUI配置/修改下面的参数值
    脚本内继承本类,实现参数定义
    请勿使用 Field.default_factory, 这将导致用户无法配置默认值
    """
    pass


P = TypeVar('P', bound=ScriptProfile)


class ScriptRuntimeArgs(BaseModel, Generic[P]):
    """运行task时,通过ScriptArgs构建, thread_function的主要参数"""
    tg_session: TgSessionArgs = Field(title='tg帐户session信息')
    profile: P = Field(title='用户在脚本中定义的Profile, 运行时产生')
    _plugins: list[GFMPlugin] = PrivateAttr(list)

    def plugins(self) -> list[GFMPlugin]:
        return self._plugins

    @classmethod
    def of(cls,
           tg_session: TgSessionArgs,
           profile: P,
           plugins_factory: Callable[['ScriptRuntimeArgs'], list[GFMPlugin]]):
        args = cls(tg_session=tg_session, profile=profile)
        args._plugins = plugins_factory(args)
        return args


class TmaParam(TypedDict):
    bot_name: str
    shot_name: str
    ref_param: str


# noinspection PyPep8Naming
def TmaParam_of(url: str) -> TmaParam | None:
    # "https://t.me/tabizoobot/tabizoo?startapp=6030741335"
    # "t.me/tabizoobot/tabizoo?startapp=6030741335"
    regex = r'(https://)?t\.me/(?P<bot_name>[^/]+)/(?P<shot_name>[^/]+)?\?startapp=(?P<ref_param>[^&]+)'
    match = re.compile(regex).match(url)
    if match:
        groups = match.groupdict()
        return TmaParam(
            bot_name=groups["bot_name"],
            shot_name=groups["shot_name"],
            ref_param=groups["ref_param"],
        )
    return None


class TeleProxyJSON(TypedDict):
    """直接用于Telethon, Pyrogram的proxy参数"""
    scheme: str  # proxy.protocol,
    hostname: str  # proxy.host,
    port: int  # proxy.port,
    username: str  # proxy.login,
    password: str  # proxy.password


# noinspection PyPep8Naming
def TeleProxyJSON_to_snapshot(proxy: TeleProxyJSON):
    return f"{proxy['scheme']}://{proxy['username']}:{proxy['password']}@{proxy['hostname']}:{proxy['port']}"
