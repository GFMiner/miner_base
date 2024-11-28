"""
Yescoin脚本示例
"""
import asyncio
from random import randint
from typing import Callable, Awaitable, Any

import aiohttp

from miner_base.model import *
from miner_base.exception import SessionException, ExecutorException, FatalExecutorException
from miner_base.plugins import *


async def thread_task(
        session: aiohttp.ClientSession,
        args: dict,
        updater: StatusUpdater,
        call_api: Callable[[CallAPIArgs], Awaitable[dict | str]],
        get_state: Callable[[str], Any],
        set_state: Callable[[str, Any], dict],
):
    """ 任务线程
    :param session: aiohttp.ClientSession
    :param args: 传入的参数
    :param updater: 用于更新状态
    :param call_api: 调用API函数
    :param get_state: 获取线程间共享的状态; value = get_state('key')
    :param set_state: 更新共享状态; set_state('key', value)
    :return: 不需要返回值
    (在App中是以协程方式并发调用的)
    """
    settings = args

    # ===
    async def _get_account_info() -> dict:
        try:
            response = await session.get(url='https://bi.yescoin.gold/account/getAccountInfo')
            response.raise_for_status()
            response_json = await response.json()
            profile_data = response_json['data']
            return profile_data
        except Exception as e:
            updater.error(f"未知错误 _get_account_info: {e}", error=e)
            raise e  # 重新抛出,交给loop处理

    async def _get_game_info():
        try:
            response = await session.get(url='https://bi.yescoin.gold/game/getGameInfo')
            response.raise_for_status()
            response_json = await response.json()
            rst = response_json['data']
            return rst
        except Exception as e:
            updater.error(f"未知错误 _get_game_info: {e}", error=e)
            raise e  # 重新抛出,交给loop处理

    async def _get_special_box_info():
        try:
            response = await session.get(url='https://bi.yescoin.gold/game/getSpecialBoxInfo')
            response.raise_for_status()
            response_json = await response.json()
            special_box_info = response_json['data']
            return special_box_info
        except Exception as e:
            updater.error(f"未知错误 _get_special_box_info: {e}", error=e)
            raise e  # 重新抛出,交给loop处理

    async def _send_taps_with_turbo() -> bool:
        try:
            special_box_info = await _get_special_box_info()
            box_type = special_box_info['recoveryBox']['boxType']
            taps = special_box_info['recoveryBox']['specialBoxTotalCount']
            await asyncio.sleep(delay=10)
            response = await session.post(url='https://bi.yescoin.gold/game/collectSpecialBoxCoin',
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

    async def _send_taps(taps: int, ) -> bool:
        try:
            response = await session.post(url='https://bi.yescoin.gold/game/collectCoin', json=taps)
            response.raise_for_status()
            response_json = await response.json()
            if not response_json['data']:
                return False
            status = response_json['data']['collectStatus']
            return status
        except Exception as e:
            updater.error(f"未知错误 _send_taps: {e}", error=e)
            raise e  # 重新抛出,交给loop处理

    async def _get_boosts_info():
        try:
            response = await session.get(url='https://bi.yescoin.gold/build/getAccountBuildInfo')
            response.raise_for_status()
            response_json = await response.json()
            boosts_info = response_json['data']
            return boosts_info
        except Exception as e:
            updater.error(f"未知错误 _get_boosts_info: {e}", error=e)
            raise e  # 重新抛出,交给loop处理

    async def _apply_energy_boost():
        try:
            response = await session.post(url='https://bi.yescoin.gold/game/recoverCoinPool')
            response.raise_for_status()
            response_json = await response.json()
            return response_json['data']
        except Exception as e:
            updater.error(f"未知错误 when _apply_energy_boost: {e}", error=e)
            await asyncio.sleep(delay=3)
            return False

    async def _apply_turbo_boost():
        try:
            response = await session.post(url='https://bi.yescoin.gold/game/recoverSpecialBox')
            response.raise_for_status()
            response_json = await response.json()
            return response_json['data']
        except Exception as e:
            updater.error(f"未知错误 _apply_turbo_boost: {e}", error=e)
            await asyncio.sleep(delay=3)
            return False

    async def _level_up(boost_id: int, ) -> bool:
        try:
            response = await session.post(url='https://bi.yescoin.gold/build/levelUp', json=boost_id)
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
        if get_state('profile_data') is None:  # 只有在登陆成功,且进入游戏获取data后才进行task
            await asyncio.sleep(2)
            continue
        updater.info(f"on loop #")
        balance = get_state('profile_data')['currentAmount']
        try:
            # 刷新状态
            taps = randint(*settings['RANDOM_TAPS_COUNT'])
            game_data = await _get_game_info()
            # game_data = await call_api(CallAPIArgs(api_name='get_game_info'))
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
            args.profile_data = profile_data
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
                        and available_energy < settings['MIN_AVAILABLE_ENERGY']
                        and settings['APPLY_DAILY_ENERGY'] is True):
                    updater.info(f"等待 5s 激活每日 能量升级")
                    await asyncio.sleep(delay=5)

                    status = await _apply_energy_boost()
                    # status = await call_api(CallAPIArgs(api_name='apply_energy_boost'))
                    if status is True:
                        updater.success(f"能量升级 完成")
                        await asyncio.sleep(delay=1)
                    continue

                if turbo_boost_count > 0 and settings['APPLY_DAILY_TURBO'] is True:
                    updater.info(f"等待 5s 激活每日 turbo boost")
                    await asyncio.sleep(delay=5)

                    if await _apply_turbo_boost():
                        updater.success(f"Turbo boost 完成")
                        await asyncio.sleep(delay=1)
                        active_turbo = True
                        # from time import time
                        # turbo_time = time()
                    continue

                if (settings['AUTO_UPGRADE_TAP'] is True
                        and balance > next_tap_price
                        and next_tap_level <= settings['MAX_TAP_LEVEL']):
                    updater.info(f"等待 5s: 准备 点击升级到 lv[ {next_tap_level} ]")
                    await asyncio.sleep(delay=5)

                    if await _level_up(boost_id=1, ):
                        updater.success(f"点击升级到 lv[ {next_tap_level} ]")
                        await asyncio.sleep(delay=1)
                    continue

                if (settings['AUTO_UPGRADE_ENERGY'] is True
                        and balance > next_energy_price
                        and next_energy_level <= settings['MAX_ENERGY_LEVEL']):
                    updater.info(f"等待 5s:准备 能量升级到 lv[ {next_energy_level} ]")
                    await asyncio.sleep(delay=5)

                    status = await _level_up(boost_id=3, )
                    if status is True:
                        updater.success(f"能量升级到 lv[ {next_energy_level} ]")
                        await asyncio.sleep(delay=1)
                    continue

                if (settings['AUTO_UPGRADE_CHARGE'] is True
                        and balance > next_charge_price
                        and next_charge_level <= settings['MAX_CHARGE_LEVEL']):
                    updater.info(f"等待 5s:准备 升级到 lv[ {next_charge_level} ]")
                    await asyncio.sleep(delay=5)

                    status = await _level_up(boost_id=2, )
                    if status is True:
                        updater.success(f"升级到 lv[ {next_charge_level} ]")
                        await asyncio.sleep(delay=1)
                    continue

                if available_energy < settings['MIN_AVAILABLE_ENERGY']:
                    updater.info(f"达到最低能量: {available_energy}: 等待 {settings['SLEEP_BY_MIN_ENERGY']}s")
                    await asyncio.sleep(delay=settings['SLEEP_BY_MIN_ENERGY'])
                    continue

        except SessionException as e:
            raise e
        except Exception as e:
            updater.error(f"未知错误: loop_task#{e}", error=e)
            await asyncio.sleep(delay=3)

        else:
            sleep_between_clicks = randint(a=settings['SLEEP_BETWEEN_TAP'][0], b=settings['SLEEP_BETWEEN_TAP'][1])

            if active_turbo is True:
                active_turbo = False

            updater.info(f"点击间隔等待[ {sleep_between_clicks} ]s")
            await asyncio.sleep(delay=sleep_between_clicks)
    pass


async def thread_auth(
        session: aiohttp.ClientSession,
        args: dict,
        updater: StatusUpdater,
        call_api: Callable[[CallAPIArgs], Awaitable[dict | str]],
        get_state: Callable[[str], Any],
        set_state: Callable[[str, Any], dict],
):
    """更新游戏状态, 包括token, YesCoinProfileData
    """
    tele_proxy = args['$tg_session']['proxy_ip']
    tma_url = args['tma_url']
    telegram_plugin: TelegramClientPlugin = args['plg_telegram_client']

    from time import time

    async def _login(tg_web_data: str, ) -> str:
        try:
            assert tg_web_data is not None, 'tg_web_data为None,获取tg数据失败'
            response = await session.post(url='https://bi.yescoin.gold/user/login',
                                          json={"code": tg_web_data})
            response.raise_for_status()
            response_json = await response.json()
            token = response_json['data']['token']
            return token
        except Exception as e:
            updater.error(f"未知错误 _login: {e}", error=e, extra={'args': f'tg_web_data#{tg_web_data}'})
            raise e  # 重新抛出,交给loop处理

    async def _get_account_info() -> dict:
        try:
            response = await session.get(url='https://bi.yescoin.gold/account/getAccountInfo')
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
                ip = await NetworkPlugin.check_proxy_ip(proxies=[tele_proxy])  # 检测proxy是否可用
                updater.info(f"on loop # Tele IP[ {ip} ]")
                # tg.login ===
                tma_token = await telegram_plugin.get_tma_token(tma_url)
                access_token = await _login(tg_web_data=tma_token)
                session.headers["Token"] = access_token
                access_token_created_time = time()
                set_state('access_token', access_token)

                # yescoin.profile ===
                profile_data = await _get_account_info()
                set_state('profile_data', profile_data)
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


async def thread_offline(
        session: aiohttp.ClientSession,
        args: dict,
        updater: StatusUpdater,
        call_api: Callable[[CallAPIArgs], Awaitable[dict | str]],
        get_state: Callable[[str], Any],
        set_state: Callable[[str, Any], dict],
):
    useragent = args['$tg_session']['useragent']

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
            async with session.request(method='POST', headers=_yes_coin_offline_header,
                                       url='https://bi.yescoin.gold/user/offline', ) as response:
                response.raise_for_status()
                response_json = await response.json()
                updater.info(f"on loop #{response_json}")
                return response_json['data']
        except Exception as e:
            updater.warning(f"未知错误 _offline(不影响task): {e}", error=e)
            await asyncio.sleep(delay=1)
            return None

    while True:
        if (tk := get_state('token')) is not None:
            await _offline(token=tk)
        await asyncio.sleep(8)  #
    pass

if __name__ == '__main__':
    """测试脚本"""
