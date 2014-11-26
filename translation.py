import os as _os
import io as _io
import json as _json

from config import config as _config

_translation = {}

if _config['gui-language'] != 'en_US':
    translation_file_path = _os.path.join('translations', _config['gui-language'] + '.json')
    with _io.open(translation_file_path, mode='r', encoding='UTF-8') as translation_file:
        _translation.update(_json.load(translation_file))


# перевести текст
def translate(text):
    return _translation.get(text, text)
