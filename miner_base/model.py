import json
import re
from abc import abstractmethod
from typing import TypedDict, Optional

from loguru import logger
from pydantic import BaseModel, Field

from miner_base.exception import *

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


class ApiDefine(BaseModel):
    """API是特殊的方法, 是直接包装接口的方法
    api调用后的返回值将直接写入data中
    api写入data的数据将保存在data作为调试辅助信息, 但在任务开始是会被移除,避免产生bug
    """
    name: str = Field('', title='API, 将用于函数调用,返回值获取')
    desc: str = Field('', title='手动填写的描述')
    raw: str = Field('', title='原始的cURL,用于手动编辑')

    base: str = Field('', title='base url')
    queries: dict = Field({}, title='查询参数')
    method: str = Field({})
    headers: dict = Field({})
    data: str = Field({}, title='post数据')
    form_data: dict = Field({}, title='表单')


class FunctionDefine(BaseModel):
    name: str = ''  # 从raw中提取的函数名
    raw: str = ''  # 原始python脚本, 将被使用exec执行
    args: dict = Field({}, title='默认参数,用于调试函数')
    is_async: bool = False  # 是否是异步函数

    @classmethod
    def of_python(cls, script: str) -> 'FunctionDefine':
        """确保用户只输入了一个函数, 提取函数名,参数列表"""
        import ast
        try:
            # 解析用户输入的代码
            tree: ast.Module = ast.parse(script)
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    return cls(
                        name=node.name,
                        raw=script,
                        is_async=isinstance(node, ast.AsyncFunctionDef), )
                logger.debug(f'非函数node#({type(node)}) {node}')
        except SyntaxError as e:
            raise InteractorArgsException(f'脚本语法错误: {e}')


class ThreadDefine(FunctionDefine, BaseModel):
    name: str = ''
    raw: str = ''  # python脚本, 将被使用exec执行
    is_async: bool = True  # thread 固定为True


class Script(BaseModel):
    """直接存储在session_state中,便于读写
    代表一个脚本对象, 在Interactor中实现业务逻辑
    """
    api: list[ApiDefine] = Field([])
    funcs: list[FunctionDefine] = Field([])
    threads: list[ThreadDefine] = Field([])
    state: dict = Field({})

    def api_by_name(self, name: str) -> ApiDefine | None:
        return next((x for x in self.api if x.name == name), None)

    def func_by_name(self, name: str) -> FunctionDefine | None:
        return next((x for x in self.funcs if x.name == name), None)

    def thread_by_name(self, name: str) -> ThreadDefine | None:
        return next((x for x in self.threads if x.name == name), None)


# 标识 to_args()阶段,对param->args 的处理方法
ScriptParamTag = Literal[
    '',  # 默认处理方法,使用json.loads将json_str转换成value值
    'random.choice',  # 用于从json_str的list中随机1个元素
    'random.choices',  # 用于从json_str的list中随机选取['ct']个元素,ct控制选取数量
    'random.sample',  # 用于从json_str的list中随机选取['ct']元素,ct控制选取数量
]


class ScriptParamField(TypedDict):
    """项目参数字段, 用于设置交互器参数;
    参见: GfProjectModel.to_args()
    属性:
    :param nm: 字段名, 用于脚本args.key
    :param dft: (json_str)字段默认值, 用于脚本args.value;
    :param tag: ScriptParamTag, 用于在to_args阶段,生成值, 默认为,使用json.loads将json_str转换成需要的参数
    --- 下面属性用于辅助生成`Param配置UI组件` ---
    :param desc: 描述, 帮助用户配置默认值
    :param tp: param类型, 不是args的类型, 因为不同的tag将导致元素被转换成不同类型(如list[str]->str)
    :param op: 是否可选, 在UI中提示用户填入值
    :param ops:list[str] (json_str); 选项, 仅当tp=list有效,控制list选项的值; 非list固定为[]
    :param ct:int 元素数量, 仅当tp=list有效,控制list选项的数量 0:任意多选 1:单选 n:指定n个多选; 非list固定为1

    注意: tp=‘str’,       ops=[‘a’,'b'],ct=n 与
         tp=‘list[str]’, ops=[‘a’,'b'],ct=n 是不同的, 前者是 st.pills, 后者是 st.multiselect

    解决生成动态值问题: 如,用户需要获得动态tma_url邀请码
        1.新增eval类型(配置参数列表,脚本加载前生成确定值)(在执行脚本前): 通过eval()动态生成值; 非常灵活,但是存在较大安全风险
        2.使用list[str]参数(不改项目代码,让脚本自行处理)(执行脚本中): 参考 range的实现
        <当前>3.新增tag属性(方案1变体)(创建task时): 在to_args()函数内,根据tag属性, 生成dft值;可用于生成随机数,设置邀请码
    """
    nm: str
    dft: str
    tag: ScriptParamTag
    desc: str
    tp: Literal['int', 'str', 'bool', 'list[int]', 'list[str]', 'list[bool]']
    op: bool
    ops: list[str]
    ct: int


# noinspection PyPep8Naming
def ScriptParamField_of_int(nm: str, desc: str, dft: int, op=False) -> ScriptParamField:
    return ScriptParamField(nm=nm, tp='int', op=op, ops=[], ct=1, dft=json.dumps(dft), desc=desc, tag='')


# noinspection PyPep8Naming
def ScriptParamField_of_str(nm: str, desc: str, dft: str, op=False, ops: list[str] = None) -> ScriptParamField:
    """ops 不为None: 代表st.pills, ct: 1单选, 0任意多选"""
    return ScriptParamField(nm=nm, tp='str', op=op, ops=ops or [], ct=1, dft=json.dumps(dft), desc=desc, tag='')


# noinspection PyPep8Naming
def ScriptParamField_of_bool(nm: str, desc: str, dft: bool, op=False) -> ScriptParamField:
    return ScriptParamField(nm=nm, tp='bool', op=op, ops=[], ct=1, dft=json.dumps(dft), desc=desc, tag='')


# noinspection PyPep8Naming
def ScriptParamField_of_tuple_2int(nm: str, desc: str, dft: tuple[int, int], op=False) -> ScriptParamField:
    """用于输入随机数的取值范围(脚本将接收tuple[int,int])"""
    return ScriptParamField(nm=nm, tp='list[int]', op=op, ops=[], ct=2, dft=json.dumps(dft), desc=desc, tag='')


# noinspection PyPep8Naming
def ScriptParamField_of_choice_list_str(nm: str, desc: str, dft: list[str], op=False) -> ScriptParamField:
    """list[str],在创建任务时(通过 random.choice)转换成str
    常用于 设置邀请码: 创建任务后,args就不再改变
    注意, random.choice得到单个元素, random.choices&ct=1 得到单个元素的list
    todo 尚未适配到UI输入控件
    """
    return ScriptParamField(nm=nm, tp='list[str]', op=op, ops=[], ct=1, dft=json.dumps(dft), desc=desc,
                            tag='random.choice')


TeleMobaiPlat = Literal['android', 'ios']


def base_tg_proj_fields_params(
        proj_dft_url='t.me/theYescoin_bot/Yescoin?startapp=1BjQUx',
) -> list[ScriptParamField]:
    """所有tg项目都必填的参数"""
    return [ScriptParamField_of_str('tma_url', 'tg小程序URL, 包含邀请码', proj_dft_url, op=False),
            ]


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
