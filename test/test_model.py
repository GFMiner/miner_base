from miner_base import State


def test_state():
    s = State({})
    r = s.get('state', None)
    print(r)


if __name__ == '__main__':
    test_state()
