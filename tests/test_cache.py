import time
import unittest

from cache import Cache


class TestCache(unittest.TestCase):
    def test_cache_01(self):
        honey_pot = []

        @Cache.cover
        def f(x):
            honey_pot.append("honey")
            return x*2

        f(3)  # will compute f(3) and store the result.
        assert honey_pot == ["honey"]

        f(3)  # f should not be invoked again.
        assert honey_pot == ["honey"]


    def test_cache_02(self):
        honey_pot = []

        @Cache.cover(ttl=1)
        def f(x):
            honey_pot.append("honey")
            return x*2

        f(3)  # will compute f(3) and store the result.
        assert honey_pot == ["honey"]

        time.sleep(1)  # wait until the cache is expired.

        f(3)  # f should be invoked again.
        assert honey_pot == ["honey", "honey"]



if __name__ == '__main__':
    unittest.main()
