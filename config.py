from typing import Any

class Config:
    def __init__(self) -> None:
        self.data = {}

    def __getitem__(self, k: str) -> Any:
        if k == "":
            return self.data
        l = k.split(".")
        r = self.data
        for i in range(len(l)-1):
            r = r[l[i]]
        try:
            return r[l[-1]]
        except KeyError:
            return None
    
    def __setitem__(self, k: str, v):
        if k == "" and isinstance(v, dict):
            self.data = v
        l = k.split(".")
        r = self.data
        for i in range(len(l)-1):
            s = l[i]
            if s in r:
                r = r[s]
            else:
                r[s] = {}
                r = r[s]
        r[l[-1]] = v
    
    def get(self, key: str, default=None) -> Any:
        i = self[key]
        return default if i == None else i
    
    def set(self, key: str, value):
        self[key] = value
    
    def __str__(self) -> str:
        return str(self.data)
    
    def __repr__(self) -> str:
        return str(self.data)

if __name__ == "__main__":
    c = Config()
    c["test.meow"] = 5
    print(c)
    print(c["test.meow"])
    c.set("cat.meow", "uwu")
    print(c.get("cat.meow"))
    print(c)
