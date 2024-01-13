import os

def reverse(text: str) -> str:
    return text[::-1]

class ArtifactParseException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class Artifact:
    def __init__(self, group: str, id: str, ver: str, file: str) -> None:
        self.group = group
        self.id = id
        self.ver = ver
        self.file = file

    def __str__(self) -> str:
        return ":".join([self.group, self.id, self.ver])
    
    def __repr__(self) -> str:
        return str(self)
    
    def __radd__(self, other):
        return other + str(self)
    
    def get_file(self) -> str:
        return self.group.replace(".", os.sep)+os.sep+self.id+os.sep+self.ver+os.sep+self.file
    
    @staticmethod
    def parse(text: str) -> "Artifact":
        # dev/m2d/gr/test/8/test-8.jar
        try:
            rt: str = reverse(text)
            ls = rt.split("/")
            file: str = reverse(ls[0])
            ver: str = reverse(ls[1])
            a_id: str = reverse(ls[2])
            rg = ".".join(ls[3:])
            group: str = reverse(rg)
            return Artifact(group, a_id, ver, file)
        except Exception as e:
            raise ArtifactParseException("Failed to parse artifact "+text, e)
