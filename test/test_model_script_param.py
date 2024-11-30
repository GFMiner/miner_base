from examples.ex_tg_yescoin import Profile
from miner_base import ScriptParam


def test_model_validate():
    raw = {
        "tg_session": {
            "id": 1, "session_name": "856",
            "proxy_ip": "socks5://f:q.5@13.54.11.60:0001",
            "agent_info": {
                "useragent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/117.0.2045.48 Version/17.0 Mobile/15E148 Safari/604.1",
                "percent": 100.0, "type": "mobile", "system": "Edge Mobile 117.0 iOS", "browser": "edge",
                "version": 117.0,
                "os": "ios"}
        },
        "profiles": {}}

    params = ScriptParam[Profile].model_validate(raw)

    print(params)
