"Module that takes care of files and paths."

from pathlib import Path


class File:
    """Here we provide convenience methods to deal with files.

    Parameters
    ----------
    path : Path
    is_directory : bool, optional

    Attributes
    ----------
    path : Path
    is_directory : bool, optional
    """

    def __init__(self, path, is_directory=False):
        self.path = Path(path).expanduser()
        self.is_directory = is_directory


    def ensure(self):
        "Ensure that path exists."

        if self.is_directory:
            self.path.mkdir(parents=True, exist_ok=True)
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.touch(exist_ok=True)


    def join(self, name):
        """If path is a directory, then join with name to form a
        subdirectory. Otherwise, just return the path.

        Parameters
        ----------
        name : str
            The child file or directory name.
        """

        if self.is_directory:
            return self.path / name

        return self.path
