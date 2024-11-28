import asyncio

from miner_base import *  # 导入基础依赖


def func_add(a, b):
    """普通函数"""
    return a + b


async def func_async_add(a, b):
    """普通异步函数"""
    await asyncio.sleep(2)
    return a + b


async def thread_task(args: dict, updater: StatusUpdater, state: State, caller: APICaller, ):
    """线程函数脚本
    1. 函数名必须以 `thread_` 开头, 否则无法被识别为线程函数
    2. 参数
        :param args: 传入的参数
        :param updater: 用于更新状态(相当于logger)
        :param caller: 发起网络请求/调用API函数
        :param state: 存储线程间共享的状态, 可以get或set
    3. 脚本在App中将以协程方式并发调用, 一个脚本可以有多个 `thread_` 函数, 它们将并发运行
    """
    add_num = args['ADD_NUM']  # 从args中读取配置
    count = 1  # 在脚本内定义变量
    while True:
        await asyncio.sleep(2)  # 使用await函数
        count = func_add(count, add_num)
        state.set('shared_count', count)  # 暂时保存
        updater.success(f'成功 +{add_num}')  # 将展示在GUI与日志中
        if count > 5:
            updater.success('任务完成')
            return


if __name__ == '__main__':
    """在这里定义的内容将不会被App执行, 可以用于测试单个函数"""


    async def test_run():
        from loguru import logger
        from miner_base.impl import LoggerStatusUpdater
        await thread_task(
            args={'ADD_NUM': 4,
                  },
            updater=LoggerStatusUpdater(logger=logger), state=State({}), caller=None,
            # state=State({}),
            # caller=APICaller(),
        )


    asyncio.run(test_run())
