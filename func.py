import os
import re
from aiogram import types
import ffmpeg

# декодирование видосиков в .ogg для последующего распозниания. Вроде как whisper не работает с битрейтом выше 64k.
def video_msg_decode(video_filename: str, ogg_audio_filename: str):
    try:
        ffmpeg.input(video_filename).output(
            ogg_audio_filename,
            format="ogg",
            acodec="libvorbis",
            ab="64k",
        ).overwrite_output().run()
    except Exception as E:
        raise E
        os.remove(ogg_audio_filename)
    finally:
        os.remove(video_filename)

# обработка длинных сообщений
async def long_msg_send(
    message: types.Message, text: str, max_symbols: int = 4000
) -> None:
    if len(text) < max_symbols:
        await message.reply(text or "-")
    else:
        for i in range(0, len(text), max_symbols):
            t = text[i : i + 4000]
            await message.answer(text=t)


# расшифровка моделью в текст
def get_transcribe(model, filename: str):
    try:
        result = model.transcribe(filename)
        return result["text"]
    except Exception as E:
        raise E
    finally:
        os.remove(filename)

# смена модели с перезапуском бота
def change_model(modelname):
    pattern = r'model = \"[a-zA-Z]{1,}\"'
    replacement = f'model = "{modelname}"'

    with open('config.py', 'r') as file:
        content = file.read()

    content_new = re.sub(pattern, replacement, content)

    with open('config.py', 'w') as file:
        file.write(content_new)

def self_restart():
    os.system('sudo /usr/bin/systemctl restart comrade-major')
