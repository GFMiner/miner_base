"""
简单脚本示例1
- [ ] 不使用 args: Profile自定义参数, 没有Profile类定义, thread函数直接使用ScriptRuntimeArgs
- [v] 使用 updater: StatusUpdater, 通过 updater.success向GUI发送当前脚本执行状态
- [ ] 不使用 caller: APICaller
- [ ] 不使用 state: State
- [v] 使用自定义函数: func_add ...
"""
import asyncio

from miner_base import *  # 导入基础依赖


def func_add(a, b):
    """普通函数"""
    return a + b


async def thread_task(args: ScriptRuntimeArgs, updater: StatusUpdater, caller: APICaller, state: State):
    """线程函数脚本
    1. 函数名必须以 `thread_` 开头, 否则无法被识别为线程函数
    2. 参数
        :param args: 传入的参数, 包含固定传入的数据
        :param updater: 用于更新状态(相当于logger)
        :param caller: 发起网络请求/调用API函数
        :param state: 存储线程间共享的状态, 可以get或set
    3. 脚本在App中将以协程方式并发调用, 一个脚本可以有多个 `thread_` 函数, 它们将并发运行
    """
    # 在脚本内定义变量
    add_num = 3
    count = 1
    while True:
        # === 等待2s : 模拟耗时操作
        await asyncio.sleep(2)

        # === 普通计算
        count = func_add(count, add_num)

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
            args=ScriptRuntimeArgs(),
            updater=LoggerStatusUpdater(logger=logger),
            state=State({}),
            caller=APICaller(),
        )


    asyncio.run(test_run())
