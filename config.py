import io as _io
import json as _json

config = {
    'announcement-token': 'fileman',
    'announcement-port': 27072,
    'connection-port': 27073,
    'connection-timeout': 3.0,
    'heartbeat-interval': 0.5,
    'root-directory': '',
    'log-file': 'log.txt',
    'users-database': 'users.json',
}

with _io.open('config.json', mode='r', encoding='UTF-8') as config_file:
    config.update(_json.load(config_file))

