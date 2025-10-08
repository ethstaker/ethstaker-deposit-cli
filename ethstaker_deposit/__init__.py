from importlib.resources import files

__version__ = files(__package__).joinpath("VERSION").read_text().strip()
__all__ = ["__version__"]
