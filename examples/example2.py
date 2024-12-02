"""
简单脚本示例2
- [v] 使用 args: Profile自定义参数, 没有Profile类定义, thread函数直接使用ScriptRuntimeArgs
- [v] 使用 updater: StatusUpdater, 通过 updater.success向GUI发送当前脚本执行状态
- [ ] 不使用 caller: APICaller
- [ ] 不使用 state: State
- [v] 使用自定义函数: 异步函数func_async_add ...
"""
import asyncio

from miner_base import *  # 导入基础依赖


async def func_async_add(a, b):
    """普通异步函数"""
    await asyncio.sleep(2)
    return a + b


class Profile(ScriptRuntimeArgs):
    """0.脚本配置参数定义: 用户将在GUI配置/修改下面的参数值
    必须 继承 `ScriptProfile` 类; 类名不限
    使用 Field 函数,定义参数默认值与说明信息
    请勿 使用 Field.default_factory, 这将导致用户无法配置默认值
    请勿 使用 非原始类型、非Field函数(例如PrivateAttr)
    <在这里的注释信息将展示在GUI中>"""
    ADD_NUM: int = Field(3, title='每次计算增加的值, 默认值为3')


async def thread_task(args: ScriptRuntimeArgs[Profile], updater: StatusUpdater, caller: APICaller, state: State):
    """线程函数脚本
    1. 函数名必须以 `thread_` 开头, 否则无法被识别为线程函数
    2. 参数
        :param args: 传入的参数, 包含固定传入的数据
        :param updater: 用于更新状态(相当于logger)
        :param caller: 发起网络请求/调用API函数
        :param state: 存储线程间共享的状态, 可以get或set
    3. 脚本在App中将以协程方式并发调用, 一个脚本可以有多个 `thread_` 函数, 它们将并发运行
    """
    add_num = args.profile.ADD_NUM  # 从args中读取配置
    count = 1
    while True:
        # === 异步计算
        count = await func_async_add(count, add_num)

        # === 将展示在GUI与日志中
        updater.success(f'计算成功 [{count}] (+{add_num})')

        if count > 10:
            updater.success('任务完成')
            return  # 脚本主动结束


if __name__ == '__main__':
    """在这里定义的内容将不会被App执行, 可以用于测试单个函数"""


    async def test_run():
        from loguru import logger
        from miner_base.impl import LoggerStatusUpdater
        await thread_task(
            args=ScriptRuntimeArgs[Profile](  # 设置参数
                profile=Profile(ADD_NUM=5),
            ),
            updater=LoggerStatusUpdater(logger=logger),
            state=State({}),
            caller=APICaller(),
        )


    asyncio.run(test_run())
