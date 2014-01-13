#coding: utf-8

from collections import defaultdict

_clients = defaultdict(list)


def register(name, callback):
    _clients[name].append(callback)


def emit(name, data=None):
    for callback in _clients.get(name, []):
        callback(name, data)
