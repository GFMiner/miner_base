"""
Plugin是Miner的依赖项
这意味着Plugin将依赖miner数据库, (例如从数据库读取tg帐户信息)
"""
from abc import ABC, abstractmethod

from miner_base.model import StatusUpdater


class GFMPlugin(ABC):
    @classmethod
    @abstractmethod
    def plugin_id(cls) -> str:
        """指定该插件的id(名称)
        对应args中 完整的key为 <plugin_id>.<key>
        """
        pass

    @classmethod
    @abstractmethod
    def of_args(cls, args: dict, updater: StatusUpdater) -> tuple[str, 'GFMPlugin']:
        """通过脚本args参数构造实例
        :returns (<plugin_id>, <instance> )
        """
        _pid = cls.plugin_id if isinstance(cls.plugin_id, str) else cls.plugin_id()
        plugin = args[_pid]
        assert plugin is not None, f'从args读取插件[{_pid}]失败'
        return plugin


class PluginTelegram(GFMPlugin, ABC):
    plugin_id = 'plg_telegram'

    async def get_tma_token(self, tma_url: str) -> str:
        """ 获取tg对特定小程序的accessToken
        :param tma_url: 启动指定tg小程序的url
        :return: 用于登陆tma的access_token,
        """
        ...


class PluginNetwork(GFMPlugin, ABC):
    plugin_id = 'plg_network'
