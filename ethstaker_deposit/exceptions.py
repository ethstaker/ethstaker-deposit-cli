class ValidationError(Exception):
    ...


class MultiLanguageError(Exception):
    def __init__(self, languages: list[str]):
        self.languages = languages
        message = f"Multiple valid languages found: {', '.join(languages)}"
        super().__init__(message)
