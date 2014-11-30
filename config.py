import io as _io
import json as _json

config = {
    'announcement-token': 'fileman',  	# токен, который сервер рассылает клиентам
    'announcement-port': 27072,  		# порт, через который сервер обьявляет о себе
    'connection-port': 27073,  			# порт подключения
    'connection-timeout': 3.0,  		# максимальное время ожидания установки соединения
    'heartbeat-interval': 0.5,  		# интервал проверки целостности соединения
    'root-directory': '',  				# корневая директория
    'log-file': 'log.txt', 		 		# файл журнала
    'users-database': 'users.json',  	# база данных пользователей
    'gui-language': 'en_US',  			# язык пользовательского интерфейса
}

with _io.open('config.json', mode='r', encoding='UTF-8') as config_file:
    config.update(_json.load(config_file))

