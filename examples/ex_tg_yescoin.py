"""
Yescoin脚本示例

- [v] 脚本配置参数定义
- [ ] API函数定义
- [v] Thread函数定义
- [v] Thread内嵌网络请求
"""
import asyncio
from random import randint, choice

from miner_base import *


class Profile(ScriptProfile):
    """0.脚本配置参数定义: 用户将在GUI配置/修改下面的参数值
    必须 继承 `ScriptProfile` 类
    使用 Field 函数,定义参数默认值与说明信息
    请勿 使用 Field.default_factory, 这将导致用户无法配置默认值
    请勿 使用 非原始类型、非Field函数(例如PrivateAttr)
    <在这里的注释信息将展示在GUI中>
    """
    TMA_URL: list[str] = Field(['t.me/theYescoin_bot/Yescoin?startapp=1BjQUx'],
                               title='tg小程序URL', description='使用list[str]用于选择随机邀请码')
    MIN_AVAILABLE_ENERGY: int = Field(120, title='最小可用能量')
    SLEEP_BY_MIN_ENERGY: int = Field(200, title='达到最小能量后等待(s)')
    AUTO_UPGRADE_TAP: bool = Field(True, title='自动升级tap')
    MAX_TAP_LEVEL: int = Field(10, title='最大tap等级')
    AUTO_UPGRADE_ENERGY: bool = Field(True, title='自动升级能量')
    MAX_ENERGY_LEVEL: int = Field(10, title='最大能量等级')
    AUTO_UPGRADE_CHARGE: bool = Field(True, title='自动升级充电')
    MAX_CHARGE_LEVEL: int = Field(10, title='最大充电等级')
    APPLY_DAILY_ENERGY: bool = Field(True, title='每日能量')
    APPLY_DAILY_TURBO: bool = Field(True, title='每日加速')
    RANDOM_TAPS_COUNT: tuple[int, int] = Field((30, 180), title='随机点击次数')
    SLEEP_BETWEEN_TAP: tuple[int, int] = Field((20, 35), title='随机点击间隔(s)')


async def thread_task(args: ScriptRuntimeArgs[Profile], updater: StatusUpdater, caller: APICaller, state: State, ):
    """1.任务线程定义:
    :param args: 传入的参数
    :param updater: 用于更新状态(相当于logger)
    :param caller: 发起网络请求/调用API函数
    :param state: 存储线程间共享的状态, 可以get或set
    :return: 不需要返回值
    脚本在App中将以 协程方式并发调用
    """
    profile: Profile = args.profile

    # ===
    # noinspection PyShadowingNames
    async def _get_account_info() -> dict:
        try:
            response = await caller.get(url='https://bi.yescoin.gold/account/getAccountInfo')
            response.raise_for_status()
            response_json = await response.json()
            profile_data = response_json['data']
            return profile_data
        except Exception as e:
            updater.error(f"未知错误 _get_account_info: {e}", error=e)
            raise e  # 重新抛出,交给loop处理

    # noinspection PyShadowingNames
    async def _get_game_info():
        try:
            response = await caller.get(url='https://bi.yescoin.gold/game/getGameInfo')
            response.raise_for_status()
            response_json = await response.json()
            rst = response_json['data']
            return rst
        except Exception as e:
            updater.error(f"未知错误 _get_game_info: {e}", error=e)
            raise e  # 重新抛出,交给loop处理

    # noinspection PyShadowingNames
    async def _get_special_box_info():
        try:
            response = await caller.get(url='https://bi.yescoin.gold/game/getSpecialBoxInfo')
            response.raise_for_status()
            response_json = await response.json()
            special_box_info = response_json['data']
            return special_box_info
        except Exception as e:
            updater.error(f"未知错误 _get_special_box_info: {e}", error=e)
            raise e  # 重新抛出,交给loop处理

    # noinspection PyShadowingNames
    async def _send_taps_with_turbo() -> bool:
        try:
            special_box_info = await _get_special_box_info()
            box_type = special_box_info['recoveryBox']['boxType']
            taps = special_box_info['recoveryBox']['specialBoxTotalCount']
            await asyncio.sleep(delay=10)
            response = await caller.post(url='https://bi.yescoin.gold/game/collectSpecialBoxCoin',
                                         json={'boxType': box_type, 'coinCount': taps})
            response.raise_for_status()
            response_json = await response.json()
            if not response_json['data']:
                return False
            status = response_json['data']['collectStatus']
            return status
        except Exception as e:
            updater.error(f"未知错误 when Tapping: {e}", error=e)
            raise e  # 重新抛出,交给loop处理

    # noinspection PyShadowingNames
    async def _send_taps(taps: int, ) -> bool:
        try:
            response = await caller.post(url='https://bi.yescoin.gold/game/collectCoin', json=taps)
            response.raise_for_status()
            response_json = await response.json()
            if not response_json['data']:
                return False
            status = response_json['data']['collectStatus']
            return status
        except Exception as e:
            updater.error(f"未知错误 _send_taps: {e}", error=e)
            raise e  # 重新抛出,交给loop处理

    # noinspection PyShadowingNames
    async def _get_boosts_info():
        try:
            response = await caller.get(url='https://bi.yescoin.gold/build/getAccountBuildInfo')
            response.raise_for_status()
            response_json = await response.json()
            boosts_info = response_json['data']
            return boosts_info
        except Exception as e:
            updater.error(f"未知错误 _get_boosts_info: {e}", error=e)
            raise e  # 重新抛出,交给loop处理

    # noinspection PyShadowingNames
    async def _apply_energy_boost():
        try:
            response = await caller.post(url='https://bi.yescoin.gold/game/recoverCoinPool')
            response.raise_for_status()
            response_json = await response.json()
            return response_json['data']
        except Exception as e:
            updater.error(f"未知错误 when _apply_energy_boost: {e}", error=e)
            await asyncio.sleep(delay=3)
            return False

    # noinspection PyShadowingNames
    async def _apply_turbo_boost():
        try:
            response = await caller.post(url='https://bi.yescoin.gold/game/recoverSpecialBox')
            response.raise_for_status()
            response_json = await response.json()
            return response_json['data']
        except Exception as e:
            updater.error(f"未知错误 _apply_turbo_boost: {e}", error=e)
            await asyncio.sleep(delay=3)
            return False

    # noinspection PyShadowingNames
    async def _level_up(boost_id: int, ) -> bool:
        try:
            response = await caller.post(url='https://bi.yescoin.gold/build/levelUp', json=boost_id)
            response.raise_for_status()
            response_json = await response.json()
            return response_json['data']
        except Exception as e:
            updater.error(f"未知错误 _level_up {boost_id} Boost: {e}", error=e)
            await asyncio.sleep(delay=3)
            return False

    # ===
    active_turbo = False
    while True:
        if state.get('profile_data') is None:  # 只有在登陆成功,且进入游戏获取data后才进行task
            await asyncio.sleep(2)
            continue
        updater.info(f"thread_task-on loop")
        balance = state.get('profile_data')['currentAmount']
        try:
            # 刷新状态
            taps = randint(*profile.RANDOM_TAPS_COUNT)
            game_data = await _get_game_info()
            # game_data = await call_api(RequestOptions(api_name='get_game_info'))
            available_energy = game_data['coinPoolLeftCount']
            coins_by_tap = game_data['singleCoinValue']
            if active_turbo:
                # taps += arguments['ADD_TAPS_ON_TURBO']
                status = await _send_taps_with_turbo()
            else:
                if taps * coins_by_tap >= available_energy:
                    taps = abs(available_energy // 10 - 1)
                status = await _send_taps(taps=taps, )
            profile_data = await _get_account_info()
            if not profile_data or not status:
                continue
            state.set('profile_data', profile_data)
            new_balance = profile_data['currentAmount']
            calc_taps = new_balance - balance
            balance = new_balance
            total = profile_data['totalAmount']
            updater.success(f"点击完成! | 余额: {balance} (+{calc_taps}) | 总数: {total}")
            boosts_info = await _get_boosts_info()

            turbo_boost_count = boosts_info['specialBoxLeftRecoveryCount']
            energy_boost_count = boosts_info['coinPoolLeftRecoveryCount']

            next_tap_level = boosts_info['singleCoinLevel'] + 1
            next_energy_level = boosts_info['coinPoolTotalLevel'] + 1
            next_charge_level = boosts_info['coinPoolRecoveryLevel'] + 1

            next_tap_price = boosts_info['singleCoinUpgradeCost']
            next_energy_price = boosts_info['coinPoolTotalUpgradeCost']
            next_charge_price = boosts_info['coinPoolRecoveryUpgradeCost']

            if active_turbo is False:
                if (energy_boost_count > 0
                        and available_energy < profile.MIN_AVAILABLE_ENERGY
                        and profile.APPLY_DAILY_ENERGY is True):
                    updater.info(f"等待 5s 激活每日 能量升级")
                    await asyncio.sleep(delay=5)

                    status = await _apply_energy_boost()
                    # status = await call_api(RequestOptions(api_name='apply_energy_boost'))
                    if status is True:
                        updater.success(f"能量升级 完成")
                        await asyncio.sleep(delay=1)
                    continue

                if turbo_boost_count > 0 and profile.APPLY_DAILY_TURBO is True:
                    updater.info(f"等待 5s 激活每日 turbo boost")
                    await asyncio.sleep(delay=5)

                    if await _apply_turbo_boost():
                        updater.success(f"Turbo boost 完成")
                        await asyncio.sleep(delay=1)
                        active_turbo = True
                        # from time import time
                        # turbo_time = time()
                    continue

                if (profile.AUTO_UPGRADE_TAP is True
                        and balance > next_tap_price
                        and next_tap_level <= profile.MAX_TAP_LEVEL):
                    updater.info(f"等待 5s: 准备 点击升级到 lv[ {next_tap_level} ]")
                    await asyncio.sleep(delay=5)

                    if await _level_up(boost_id=1, ):
                        updater.success(f"点击升级到 lv[ {next_tap_level} ]")
                        await asyncio.sleep(delay=1)
                    continue

                if (profile.AUTO_UPGRADE_ENERGY is True
                        and balance > next_energy_price
                        and next_energy_level <= profile.MAX_ENERGY_LEVEL):
                    updater.info(f"等待 5s:准备 能量升级到 lv[ {next_energy_level} ]")
                    await asyncio.sleep(delay=5)

                    status = await _level_up(boost_id=3, )
                    if status is True:
                        updater.success(f"能量升级到 lv[ {next_energy_level} ]")
                        await asyncio.sleep(delay=1)
                    continue

                if (profile.AUTO_UPGRADE_CHARGE is True
                        and balance > next_charge_price
                        and next_charge_level <= profile.MAX_CHARGE_LEVEL):
                    updater.info(f"等待 5s:准备 升级到 lv[ {next_charge_level} ]")
                    await asyncio.sleep(delay=5)

                    status = await _level_up(boost_id=2, )
                    if status is True:
                        updater.success(f"升级到 lv[ {next_charge_level} ]")
                        await asyncio.sleep(delay=1)
                    continue

                if available_energy < profile.MIN_AVAILABLE_ENERGY:
                    updater.info(f"达到最低能量: {available_energy}: 等待 {profile.SLEEP_BY_MIN_ENERGY}s")
                    await asyncio.sleep(delay=profile.SLEEP_BY_MIN_ENERGY)
                    continue

        except SessionException as e:
            raise e
        except Exception as e:
            updater.error(f"未知错误: loop_task#{e}", error=e)
            await asyncio.sleep(delay=3)

        else:
            sleep_between_clicks = randint(*profile.SLEEP_BETWEEN_TAP)

            if active_turbo is True:
                active_turbo = False

            updater.info(f"点击间隔等待[ {sleep_between_clicks} ]s")
            await asyncio.sleep(delay=sleep_between_clicks)
    pass


async def thread_auth(args: ScriptRuntimeArgs[Profile], updater: StatusUpdater, caller: APICaller, state: State, ):
    """更新游戏状态: 每1小时刷新用户auth信息
     包括token
    """
    tele_proxy = args.tg_session['proxy_ip']
    tma_url = choice(args.profile.TMA_URL)  # 随机选一个
    telegram_plugin = PluginTelegram.of_args(args, updater)
    net_plugin = PluginNetwork.of_args(args, updater)

    from time import time

    # noinspection PyShadowingNames
    async def _login(tg_web_data: str, ) -> str:
        try:
            assert tg_web_data is not None, 'tg_web_data为None,获取tg数据失败'
            response = await caller.post(url='https://bi.yescoin.gold/user/login',
                                         json={"code": tg_web_data})
            response.raise_for_status()
            response_json = await response.json()
            token = response_json['data']['token']
            return token
        except Exception as e:
            updater.error(f"未知错误 _login: {e}", error=e, extra={'args': f'tg_web_data#{tg_web_data}'})
            raise e  # 重新抛出,交给loop处理

    # noinspection PyShadowingNames
    async def _get_account_info() -> dict:
        try:
            response = await caller.get(url='https://bi.yescoin.gold/account/getAccountInfo')
            response.raise_for_status()
            response_json = await response.json()
            profile_data = response_json['data']
            return profile_data
        except Exception as e:
            updater.error(f"未知错误 _get_account_info: {e}", error=e)
            raise e  # 重新抛出,交给loop处理

    access_token_created_time = 0
    while True:
        if time() - access_token_created_time >= 3600:  # 每小时更新
            try:
                ip = await net_plugin.check_proxy_ip(proxies=[tele_proxy])  # 检测proxy是否可用
                updater.info(f"on loop # Tele IP[ {ip} ]")
                # tg.login ===
                tma_token = await telegram_plugin.get_tma_token(tma_url)
                access_token = await _login(tg_web_data=tma_token)
                updater.debug('获得token#', extra={'token': access_token})
                caller.session.headers["Token"] = access_token
                access_token_created_time = time()
                state.set('access_token', access_token)

                # yescoin.profile ===
                profile_data = await _get_account_info()
                state.set('profile_data', profile_data)
            except FatalExecutorException as e:
                raise e
            except ExecutorException as e:  # 普通错误(断网等), 尝试sleep后重试
                updater.error(f"{e}", error=e)
                await asyncio.sleep(30)
            except Exception as e:
                updater.error(f"未知错误 {type(e)}: {e}", error=e)
                raise e  # 未知的错误等同严重错误,尝试退出任务
        else:
            await asyncio.sleep(60)  # 每分钟检查一次
    pass


async def thread_offline(args: ScriptRuntimeArgs[Profile], updater: StatusUpdater, caller: APICaller, state: State, ):
    useragent = args.tg_session['agent_info']['useragent']

    async def _offline(token: str, ) -> str | None:
        """活跃时每8s发送一次;否则1分钟一次"""
        _yes_coin_offline_header = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,hmn;q=0.6",
            "content-length": "0",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.yescoin.gold",
            "priority": "u=1, i",
            "referer": "https://www.yescoin.gold/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "token": token,
            "user-agent": useragent
        }
        try:
            async with caller.post(url='https://bi.yescoin.gold/user/offline',
                                   headers=_yes_coin_offline_header, ) as response:
                response.raise_for_status()
                response_json = await response.json()
                updater.info(f"on loop #{response_json}")
                return response_json['data']
        except Exception as e:
            updater.warning(f"未知错误 _offline(不影响task): {e}", error=e)
            await asyncio.sleep(delay=1)
            return None

    while True:
        if (tk := state.get('token')) is not None:
            await _offline(token=tk)
        await asyncio.sleep(8)  #
    pass


if __name__ == '__main__':
    """
    可以在这里编写简单函数测试用例
    完整测试使用App运行, 插件(Plugin)只有在App中运行才会加载
    """
