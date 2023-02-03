
try:
    from collections.abc import Hashable
except ImportError:
    from collections import Hashable

from functools import partial

import time

from typing import Callable




_infinity = float('inf')

class Cache:

    _functions_dict: dict[Callable, dict] = {}

    @classmethod
    def cover(cls, function: Callable = None, /, ttl=60*60):
        return cls._cover(function=function, ttl=ttl) if function else partial(cls._cover, ttl=ttl)

    @classmethod    
    def _cover(cls, function: Callable, ttl: int):

        _caches = {}
        _time_to_lives = {}

        def wrapper(*args, **kwargs):
            sentinel = object()
            key = cls._make_key(*args, **kwargs)
            result = _caches.get(key, sentinel)
            time_to_live = _time_to_lives.get(key, _infinity)
            if result is not sentinel and not cls._is_time_exceeded(time_to_live):
                return result
            result = function(*args, **kwargs)
            _caches[key] = result
            _time_to_lives[key] = (time.time() + ttl)
            return result

        cls._functions_dict[wrapper] = {
            'caches': _caches,
            'time_to_lives': _time_to_lives,
        }

        return wrapper

    
    @staticmethod
    def _is_time_exceeded(time_to_live: int):
        return time.time() > time_to_live


    @staticmethod
    def _make_key(*args, **kwargs):
        if kwargs:
            kwargs = sorted(kwargs)
        
        key = []
        for arg in args:
            if isinstance(arg, Hashable):
                key.append(arg)
            else:
                raise ValueError

        for k, v in kwargs.items():
            if isinstance(v, Hashable):
                key.append((k, v))
            else:
                raise ValueError

        return tuple(key)

