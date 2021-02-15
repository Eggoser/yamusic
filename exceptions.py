class MP3FileSaveError(Exception):
    def __init__(self, message="Не удалось сохранить файл"):
        self.message = message
        super().__init__(self.message)


class MP3TagCreateError(Exception):
    def __init__(self, message="Mutagen не смог инициализировать теги"):
        self.message = message
        super().__init__(self.message)


class DirectoryNotFound(Exception):
    def __init__(self, message="Каталог не существует"):
        self.message = message
        super().__init__(self.message)
