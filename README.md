# GFMiner base组件

## 创建GFMiner脚本

### 0.环境&基础

> python > 3.11 (建议使用 3.12)

- 掌握基本语法: 控制流程(if,while,for),函数定义(def),类定义(class)
- 掌握基本asyncio用法: async def, await

> aiohttp > 3.10 (建议使用 3.10.10)

- 能够使用aiohttp发起网络请求(get, post)
- 能够修改请求头(headers), 请求参数(params), 请求体(data)

> pydantic > 2.9 (建议使用 3.9.2)

- 会使用 BaseModel, Field(default=默认参数, title='描述')

### 1.安装依赖

```text
# requirements.txt
git+https://github.com/GFMiner/miner_base.git
```

### 2.编写脚本

> 更多示例参见 `examples/`, 
> [新手查看示例1](examples/example1.py)
> [老手查看示例3](examples/example3.py)
> [真实案例YesCoin](examples/example4_tg_yescoin.py)
 

```python
"""
极简示例
"""
import asyncio

from miner_base import *


async def thread_task(args: ScriptRuntimeArgs, updater: StatusUpdater, caller: APICaller, state: State):
    """线程函数脚本
    函数名必须以 `thread_` 开头, 否则无法被识别为线程函数
    """
    # 在脚本内定义变量
    count = 1
    while True:
        # === 等待2s : 模拟耗时操作
        await asyncio.sleep(2)

        # === 运算逻辑
        count += 3

        # === 将展示在GUI与日志中
        updater.success(f'计算成功 [{count}]')

        if count > 10:
            updater.success('任务完成')
            return  # 退出函数, 无需返回值, 脚本主动结束
```

### 3.将脚本导入到APP

在`脚本工具`中调试脚本
- [GFM脚本开发资源包](https://drive.google.com/file/d/14JC37niBRixKHq7P5NoH_JAsluHetLVT/view?usp=drive_link)

