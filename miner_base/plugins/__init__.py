"""
Plugin是Miner的依赖项
这意味着Plugin将依赖miner数据库, (例如从数据库读取tg帐户信息)
"""
from abc import ABC, abstractmethod

from miner_base.model import StatusUpdater, ScriptParam


class GFMPlugin(ABC):

    @classmethod
    @abstractmethod
    def of_args(cls, args: ScriptParam, updater: StatusUpdater):
        """通过脚本args参数构造实例
        1种Class只能注册1个实例
        :returns plugin
        """
        plugin = [p for p in args.plugins if isinstance(p, cls)]
        assert len(plugin) != 0, f'从args读取插件[{cls}]失败'
        return plugin[0]


class PluginTelegram(GFMPlugin, ABC):

    async def get_tma_token(self, tma_url: str) -> str:
        """ 获取tg对特定小程序的accessToken
        :param tma_url: 启动指定tg小程序的url
        :return: 用于登陆tma的access_token,
        """
        ...


class PluginNetwork(GFMPlugin, ABC):
    ...
