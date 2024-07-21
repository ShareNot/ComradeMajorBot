import asyncio
import os
import pathlib

from random import choice

import ffmpeg

from aiogram import Bot
from aiogram import Dispatcher
from aiogram import types
from aiogram.filters.command import Command, CommandObject
from aiogram import F

import torch
import whisper

from func import video_msg_decode
from func import long_msg_send
from func import get_transcribe
from func import change_model
from func import self_restart
from config import Config

voice_dir = Config.dirs.get("voice")
audio_dir = Config.dirs.get("audio")
models_dir = Config.dirs.get("models")
video_dir = Config.dirs.get("video")
modellist = Config.modellist
whitelist = Config.whitelist
adminlist = Config.adminlist

# определяем есть ли видак в серваке. Еси нет - живём на CPU и страдаем.
device = "cuda" if torch.cuda.is_available() else "cpu"

# загружаем модель, которая указана в конфиге, с учётом девайса для обработки и с указанием директории для модели
print("Loading model...")
model = whisper.load_model(Config.model, device=device, download_root=models_dir)

# логируем успешную загрузку
print(f"Model loaded.")

# получаем токен бота из конфига
bot = Bot(token=Config.CMAJOR_TOKEN)

# сокращаем вызов диспетчера aiogram
dp = Dispatcher()

# логируем успешный запуск бота
print("CMajor started")

###

# отсеиваем сообщения по белому списку
@dp.message(lambda message: message.chat.id not in whitelist)
async def checker(message):
   await message.answer("Ты не интересен Майору.")


# реакция на start
@dp.message(Command("start"))
async def command_start(message: types.Message):
    await message.answer(f"Товарищ Майор вошёл в чат с номером {message.chat.id}")


# реакция на help
@dp.message(Command("help"))
async def command_help(message: types.Message):
    await message.reply("Для получения помощи необходимо взять талон на получение справки для очереди за талонами")

# уронить
@dp.message(Command("drop_the_major"))
async def command_drop(message: types.Message):
    phrases = [
            "Бля я упал",
            "Меня уронили",
            "Майор лежит",
            "Майор уронен",
            "Бля я уронился",
            "Я упал бля"
        ]
    await message.reply(choice(phrases))


# смена модели
@dp.message(Command('model'))
async def test(message: types.Message, command: CommandObject):
    if message.from_user.id in adminlist:
        if command.args is None:
            await message.reply(f"Доступные модели: {', '.join(modellist)}")
        elif command.args in modellist:
            await message.reply(f"Меняем модель Майора на {command.args}")
            change_model(command.args)
            self_restart()
        else:
            await message.reply(f"Модель {command.args} не найдена среди доступных")
    else:
        await message.reply(f"Ваши руки коротки чтобы достать Майора")

# # реакция на любой текст (в групповом чате будет мешать)
# @dp.message(F.text)
# async def get_text(message: types.Message):
#     await message.reply(
#         f"Ты втираешь Майору какую-то дичь"
#     )


# реакция на голосовые сообщения или на аудио в чате
@dp.message(F.voice)
@dp.message(F.audio)

# получаем и загружаем аудио
async def get_audio(message: types.Message):
    voice_object = message.voice or message.audio
    pathlib.Path(audio_dir).mkdir(parents=True, exist_ok=True)
    filename = os.path.join(audio_dir, f"{voice_object.file_unique_id}")

    # сообщаем что файл в загрузке
    mess = await message.reply("За твоим файлом уже выехали")
    try:
        await bot.download(
            voice_object,
            destination=filename,
        )
    except Exception as E:
        await message.reply(f"Ошибка! Майор не смог забрать файл.\n{E}")
        raise E
    finally:
        # удаляем предыдущее сообщение чтобы заместить его новым (так себе практика, но работает)
        await mess.delete()

    # сообщаем что файл декодируется
    mess = await message.reply("Майор уже смотрит на твой файл")
    try:
        text = get_transcribe(model, filename)
    except Exception as E:
        await message.reply("Ошибка! В файле какая-то дичь. Майор не понимает и негодует!")
        raise E
    finally:
        await mess.delete()
    await long_msg_send(message, text)


# реакция на видосики (аналогично аудио, но с предварительным декодом в .ogg)
@dp.message(F.video)
@dp.message(F.video_note)
@dp.message(F.document)
async def get_video(message: types.Message):
    pathlib.Path(video_dir).mkdir(parents=True, exist_ok=True)
    object = message.video or message.video_note or message.document

    filename = os.path.join(
        video_dir,
        f"{object.file_unique_id}",
    )

    mess = await message.reply("За твоим файлом уже выехали")
    try:
        await bot.download(
            object,
            destination=filename,
        )
    except Exception as E:
        await message.reply(f"Ошибка! Майор не смог забрать файл.\n{E}")
        raise E
    finally:
        await mess.delete()

    output_filename = filename
    if message.document:
        mess = await message.reply("Майор уже смотрит на твой файл")
        output_filename = os.path.join(
            video_dir,
            f"{object.file_unique_id}.ogg",
        )
        try:
            video_msg_decode(filename, output_filename)
        except Exception as E:
            await message.reply(f"Ошибка! В файле какая-то дичь. Майор не понимает и негодует!\n{E}")
            raise E
        finally:
            await mess.delete()

    mess = await message.reply("Майор уже пишет тебе")
    try:
        text = get_transcribe(model, output_filename)
    except Exception as E:
        await message.reply("Ошибка! Пальцы майора не смогли написать текст!")
        raise E
    finally:
        await mess.delete()
    await long_msg_send(message, text)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
