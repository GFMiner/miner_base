import time


def milliseconds() -> int:
    return time.time().__int__()
