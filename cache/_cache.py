
try:
    from collections.abc import Hashable
except ImportError:
    from collections import Hashable

from copy import deepcopy
from functools import partial
import time
import threading
from typing import Callable, Dict




_infinity = float('inf')

class Cache:

    _functions_dict: Dict[Callable, dict] = {}
    _thread_object_ = None
    _is_shutdown = False
    _sleep_time = 0

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
                return deepcopy(result)
            result = function(*args, **kwargs)
            _caches[key] = result
            _time_to_lives[key] = (time.time() + ttl)
            return deepcopy(result)

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


    @classmethod
    def _check_expiry(cls, sleep_time: int):

        class SentinelException(Exception):
            ...

        def check_expiry():
            if cls._is_shutdown:
                raise SentinelException

            copied_dict: dict = deepcopy(cls.functions_dict)
            for function, function_dict in copied_dict.items():
                for key, time_to_live in function_dict['time_to_live'].items():
                    if cls._is_key_expired(time_to_live=time_to_live):
                        cls._drop_key(function, key)
            threading.Timer(sleep_time, check_expiry).start()

        try:
            check_expiry()
        except SentinelException:
            return


    @classmethod
    def _drop_key(cls, function: Callable, key):
        del cls.functions_dict[function]['cache'][key]
        del cls.functions_dict[function]['time_to_live'][key]

    @classmethod
    def start(cls, sleep_time: int = 0):
        cls._sleep_time = sleep_time
        cls._is_shutdown = False
        cls._thread_object_ = threading.Thread(target=partial(cls._check_expiry, sleep_time=sleep_time))
        cls._thread_object_.daemon = True
        cls._thread_object_.start()

    @classmethod
    def get_info(cls, *, function) -> dict:
        return cls.functions_dict[function]

    @classmethod
    def shutdown(cls):
        cls._is_shutdown = True

    @classmethod
    def reset(cls):
        cls.functions_dict = {}
        cls.shutdown()
        cls._thread_object_ = None
        if cls._sleep_time:
            time.sleep(cls._sleep_time)
