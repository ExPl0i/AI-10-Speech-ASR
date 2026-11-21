"""Перевод длинных фраз группы в одинаковый формат для занятия «Распознавание речи».

Записи голоса – персональные данные: скрипт запускается на школьном компьютере, результат хранится
на школьном носителе и не выкладывается в открытый доступ.

Вход – папка с подпапками учеников; в каждой – записи фраз с телефона в любом формате (m4a, mp3, ogg, opus, amr, wav)
и рядом с каждой записью текстовый файл с тем же именем и точной расшифровкой: «фраза1.m4a» и «фраза1.txt».
Выход – data/phrases/<ученик>/<имя>.wav (WAV, 16 000 Гц, моно, 16 бит) и <имя>.txt в кодировке UTF-8.
Нужна программа ffmpeg (ffmpeg.org; в Colab уже установлена).

    python prepare_phrases.py путь/к/записям
"""
import shutil
import subprocess
import sys
from pathlib import Path

AUDIO = {'.wav', '.m4a', '.mp3', '.ogg', '.opus', '.amr', '.aac', '.3gp', '.flac', '.webm'}


def read_text(path):
    """Расшифровка в UTF-8 или в кодировке Windows (cp1251) – так сохраняет Блокнот в старых версиях."""
    raw = path.read_bytes()
    for enc in ('utf-8-sig', 'cp1251'):
        try:
            return raw.decode(enc).strip()
        except UnicodeDecodeError:
            continue
    raise ValueError(f'не удалось прочитать {path}')


def main(src_root, dst_root=Path('data') / 'phrases'):
    if shutil.which('ffmpeg') is None:
        sys.exit('ffmpeg не найден: установите его (ffmpeg.org) и добавьте в PATH')
    done, skipped = 0, []
    for student in sorted(p for p in Path(src_root).iterdir() if p.is_dir()):
        n = 0
        for f in sorted(student.iterdir()):
            if f.suffix.lower() not in AUDIO:
                continue
            txt = f.with_suffix('.txt')
            if not txt.exists():
                skipped.append(f'{f} (нет файла {txt.name})'); continue
            dst = Path(dst_root) / student.name / (f.stem + '.wav')
            dst.parent.mkdir(parents=True, exist_ok=True)
            cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-i', str(f), '-ac', '1', '-ar', '16000', '-sample_fmt', 's16', str(dst)]
            if subprocess.run(cmd).returncode != 0:
                skipped.append(f'{f} (файл не читается)'); continue
            dst.with_suffix('.txt').write_text(read_text(txt), encoding='utf-8')
            n += 1; done += 1
        print(f'{student.name}: {n} фраз')
    print('всего:', done)
    if skipped:
        print('пропущены:', *skipped, sep='\n  ')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
