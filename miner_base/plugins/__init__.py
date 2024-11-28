"""
Plugin是Miner的依赖项
这意味着Plugin将依赖miner数据库, (例如从数据库读取tg帐户信息)
"""
from abc import ABC, abstractmethod


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
    def of_args(cls, args:dict):
        """通过脚本args参数构造实例
        """
        pass

