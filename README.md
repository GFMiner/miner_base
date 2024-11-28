# GFMiner base组件

## 创建GFMiner脚本

### 条件
python > 3.11

### 1.安装依赖

```text
# requirements.txt
git+https://github.com/GFMiner/miner_base.git
```

### 2.编写脚本

> 更多示例参见 `examples/`, [示例代码1](examples/example1.py)

```python
"""
极简示例
"""
import asyncio

from miner_base import *


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
        count += add_num
        state.set('shared_count', count)  # 暂时保存
        updater.success('成功+1')  # 将展示在GUI与日志中
        if count > 5:
            updater.success('任务完成')
            return 
```

### 3.将脚本导入到APP
