"""Подготовка к занятию «Распознавание речи» (запускать на компьютере с интернетом).

Скачивает в папку models модели, чтобы в аудитории ноутбук работал без интернета:
    vosk-model-small-ru-0.22           – Vosk для русского языка, 45 МБ (Apache 2.0);
    openai/whisper-tiny, whisper-base  – Whisper для процессора, около 0,5 ГБ вместе (MIT);
    openai/whisper-small               – только с ключом --small, около 1 ГБ (для Colab он скачивается сам);
и озвучивает 20 запасных фраз водителя синтезатором Piper двумя голосами в data/reserve_tts.
Нужны библиотеки: pip install vosk transformers piper-tts
    python prepare_data.py [--small]
"""
import sys
import urllib.request
import wave
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent
MODELS, TTS_DIR = ROOT / 'models', ROOT / 'data' / 'reserve_tts'
PHRASES = [
    'построй маршрут до улицы весенней дом двадцать пять', 'сколько километров до кемерово',
    'поверни направо через триста метров', 'установи температуру двадцать два градуса',
    'позвони саше', 'включи радио сто четыре и восемь', 'найди заправку на кузнецком проспекте',
    'какое давление в передних шинах', 'едем на проспект ленина дом сорок семь', 'сделай потеплее на два градуса',
    'включи следующую песню', 'сколько бензина осталось в баке', 'остановись у дома номер девятнадцать',
    'построй маршрут до притомского проспекта', 'через сколько минут мы приедем', 'выключи кондиционер',
    'позвони маме на мобильный', 'какая скорость разрешена на улице кирова', 'открой окно водителя',
    'едем в аэропорт имени леонова']
VOICES = ['irina', 'denis']


def vosk_model():
    target = MODELS / 'vosk-model-small-ru-0.22'
    if target.exists():
        return print('уже есть:', target)
    MODELS.mkdir(exist_ok=True)
    print('скачиваю Vosk ...')
    urllib.request.urlretrieve('https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip', MODELS / 'vosk.zip')
    zipfile.ZipFile(MODELS / 'vosk.zip').extractall(MODELS)
    (MODELS / 'vosk.zip').unlink()


def whisper_models(names):
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    for name in names:
        target = MODELS / name.split('/')[-1]
        if (target / 'config.json').exists():
            print('уже есть:', target); continue
        print('скачиваю', name)
        WhisperProcessor.from_pretrained(name).save_pretrained(target)
        WhisperForConditionalGeneration.from_pretrained(name).save_pretrained(target)


def reserve_tts():
    from piper import PiperVoice
    base = 'https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/{v}/medium/ru_RU-{v}-medium.onnx'
    for v in VOICES:
        onnx = MODELS / f'ru_RU-{v}-medium.onnx'
        for suffix in ('', '.json'):
            if not Path(str(onnx) + suffix).exists():
                MODELS.mkdir(exist_ok=True); urllib.request.urlretrieve(base.format(v=v) + suffix, str(onnx) + suffix)
        voice = PiperVoice.load(str(onnx))
        (TTS_DIR / v).mkdir(parents=True, exist_ok=True)
        for k, text in enumerate(PHRASES):
            with wave.open(str(TTS_DIR / v / f'{k:02d}.wav'), 'wb') as f:
                if hasattr(voice, 'synthesize_wav'):
                    voice.synthesize_wav(text, f)
                else:   # piper-tts до версии 1.3
                    voice.synthesize(text, f)
    print('озвучено:', len(VOICES) * len(PHRASES), 'фраз в', TTS_DIR)


if __name__ == '__main__':
    vosk_model()
    whisper_models(['openai/whisper-tiny', 'openai/whisper-base'] + (['openai/whisper-small'] if '--small' in sys.argv else []))
    reserve_tts()
