import os


class Config:

    # токен бота (лежит в файле .env, на который должен указывать юнит)
    CMAJOR_TOKEN = os.environ.get("CMAJOR_TOKEN")

    # белый список доступа к боту (лежит в файле .env)
    whitelist = [299999995, 38999990, -1999999994, -499999995]
    adminlist = [299999995]

    # модели whisper: large medium small base tiny
    modellist = ["large", "medium", "small", "base", "tiny"]
    model = "tiny"

    # директории для временных файлов и для загруженных моделей
    dirs = {
        "models": "./models",
        "audio": "./tmp",
        "voice": "./tmp",
        "video": "./tmp",
    }
