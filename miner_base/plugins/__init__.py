"""
Plugin是Miner的依赖项
这意味着Plugin将依赖miner数据库, (例如从数据库读取tg帐户信息)
"""
from abc import ABC

from miner_base import GFMPlugin


class PluginTelegram(GFMPlugin, ABC):

    async def get_tma_token(self, tma_url: str) -> str:
        """ 获取tg对特定小程序的accessToken
        :param tma_url: 启动指定tg小程序的url
        :return: 用于登陆tma的access_token,
        """
        ...


class PluginNetwork(GFMPlugin, ABC):
    ...
