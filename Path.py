import os
from typing import Union


class Path:
    """Java-like Path class"""
    
    def __init__(self, path_str):
        self.path: str = os.path.normpath(path_str)

    def expand_user(self):
        return Path(os.path.expanduser(self.path))


    def resolve(self, other: Union[str, "Path"]):
        if isinstance(other, str):
            new_path = os.path.normpath(os.path.join(self.path, other))
        elif isinstance(other, Path):
            new_path = os.path.normpath(os.path.join(self.path, os.path.splitdrive(other.path)[1]))
        else:
            raise ValueError("Other is not str or Path: "+str(type(other)))
        return Path(new_path)

    def get_parent(self):
        parent_dir = os.path.dirname(self.path)
        return Path(parent_dir)

    def get_file_name(self) -> str:
        return os.path.basename(self.path)
    
    def to_list(self) -> list[str]:
        return os.path.splitdrive(self.path)[1].removeprefix(os.sep).split(os.sep)
    
    def to_str(self) -> str:
        return str(self)

    def __str__(self):
        return self.path
    
    def __repr__(self) -> str:
        return str(self)
    
    def __radd__(self, other): # type: ignore
        if type(other) is str:
            return other+self.path
        elif type(other) is Path:
            other: Path = other
            drive = os.path.splitdrive(os.path.normpath(other.path))[0]
            if drive == "":
                drive = os.path.splitdrive(self.path)[0]
            return Path(drive+os.path.normpath(other.path)+os.path.splitdrive(self.path)[1])
        else:
            raise TypeError("Cannot radd "+str(type(other)))

    def __add__(self, other): # type: ignore
        if type(other) == str:
            return self.path+other
        elif type(other) is Path:
            other: Path = other
            drive = os.path.splitdrive(os.path.normpath(other.path))[0]
            if drive == "":
                drive = os.path.splitdrive(self.path)[0]
            return Path(drive+os.path.normpath(other.path)+os.path.splitdrive(self.path)[1])
        else:
            raise TypeError("Cannot add "+str(type(other)))
    
    def __iter__(self):
        return iter(self.to_list())
    
    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Path):
            return self.path == __value.path
        if isinstance(__value, str):
            return self.path == __value
        return False
    
    def __ne__(self, __value: object) -> bool:
        return not self.__eq__(__value)

if __name__ == "__main__":
    p = Path("\\dev\\test/aboba/t.cs")
    print(p)
    print(p.get_parent())
    print(p.resolve("i.md5"))
    print(p.get_file_name())
    print(p+"file.md")
    print("file"+p)
    print(p.to_list())
    for s in p:
        print(s)
    print(p == p)