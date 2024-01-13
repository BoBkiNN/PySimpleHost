from flask import Flask, Response, request, send_file, Request
import os, re, json, base64
from artifact import Artifact, ArtifactParseException
from Path import Path
import Logger

CFG_FILE = os.getcwd()+os.sep+"config.json"
BROWSER_PATTERN = re.compile("Chrome|Mozilla|Safari|Opera")
DEF_CFG = {
    "repo_path": os.getcwd()+os.sep+"repository",
    "user": "admin",
    "password": "password",
    "protect": ["put"] # All: ["download", "put", "browse"]
}
DEF_AUTH = "admin:password"

def load_cfg() -> dict:
    if os.path.isfile(CFG_FILE):
        with open(CFG_FILE, "r") as f:
            Logger.info("Loading config")
            return json.load(f)
    else:
        save_cfg(DEF_CFG)
        return DEF_CFG

def save_cfg(data: dict):
    with open(CFG_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

repo_path = Path(DEF_CFG["repo_path"])
auth = base64.b64encode(DEF_AUTH.encode()).decode()
protect = ["put"]

def reload():
    global repo_path, auth, protect
    d = load_cfg()
    repo_path = d["repo_path"]
    if repo_path == None:
        repo_path = Path(DEF_CFG["repo_path"])
    else:
        repo_path = Path(repo_path)
    user = d["user"]
    pw = d["password"]
    if user == None or pw == None:
        auth = base64.b64encode(DEF_AUTH.encode())
    else:
        auth = base64.b64encode(str.encode(user+":"+pw))
    auth = auth.decode()
    protect = d["protect"]
    if protect == None:
        protect = ["put"]

def check_access(perm: str) -> bool:
    if perm in protect:
        h = request.headers.get("Authorization", None)
        if h == None:
            return False
        if h.startswith("Basic "):
            provided = h.removeprefix("Basic ")
            return auth == provided
    else:
        return True

app = Flask("PyMavenRepo")
err404 = Response(status=404)

def errc(code: int) -> Response:
    return Response(f"<!DOCTYPE html><html><head></head><body><h1>{code}</h1></body></html>", code)

err404c = errc(404)

def is_browser(r: Request):
    return BROWSER_PATTERN.findall(r.headers["User-Agent"]) != None

def get_file(artifact: Artifact) -> Path:
    return repo_path.resolve(artifact.get_file())

def get_artifact(artifact: Artifact) -> Response:
    path = get_file(artifact)
    if os.path.isfile(path.to_str()):
        Logger.info("Sending artifact "+artifact)
        return send_file(path.to_str())
    Logger.info("Artifact not found "+artifact)
    return err404

def download_file(path: Path) -> Response:
    if os.path.isfile(path.to_str()):
        return send_file(path.to_str())
    return err404c

def indexFiles(path: Path, relative: Path) -> Response:
    p = path.to_str()
    if not os.path.isdir(p):
        return err404c
    ls = os.listdir(p)
    html = f"<!DOCTYPE html><html><head></head><body><h1>Index of {relative}:</h1><hr><ul>"
    if path != repo_path:
        html += f"<li><a href={request.host_url+relative.get_parent()}>..</a></li>"
    for f in ls:
        href = request.base_url.removesuffix("/")+"/"+f
        html += f"<li><a href={href}>{f}</a></li>"
    html += "</ul></body></html>"
    return Response(html, 200, mimetype="text/html")


def put_artifact(artifact: Artifact, r: Request) -> Response:
    # print(len(r.data), len(r.files), r.files.to_dict())
    Logger.info("Uploading artifact "+artifact+" "+artifact.file)
    target = get_file(artifact)
    os.makedirs(target.get_parent().to_str(), exist_ok=True)
    p = target.to_str()
    if os.path.exists(p):
        mode = "wb"
    else:
        mode = "xb"
    with open(p, mode) as f:
        f.write(r.data)
    return Response(status=201)

@app.route('/<path:artifact>', methods=["GET", "PUT"])
def mainRoute(artifact: str):
    path: Path = repo_path.resolve(artifact)
    if is_browser(request) and os.path.isdir(path.to_str()):
        if not check_access("browse"):
            return Response(status=401)
        Logger.info(path)
        return indexFiles(path, Path(artifact))
    try:
        a = Artifact.parse(artifact)
        if request.method == "GET":
            if not check_access("download"):
                return Response(status=401)
            return get_artifact(a)
        elif request.method == "PUT":
            if not check_access("put"):
                return Response(status=401)
            return put_artifact(a, request)
    except ArtifactParseException as e:
        if is_browser(request):
            Logger.info(path)
            if os.path.isdir(path.to_str()):
                if not check_access("browse"):
                    return Response(status=401)
                return indexFiles(path, Path(artifact))
            else:
                if not check_access("download"):
                    return Response(status=401)
                return download_file(Path(artifact))
        Logger.warn("Not an artifact: "+str(e))
        return err404
    return err404

@app.route("/")
def root():
    if is_browser(request):
        if not check_access("browse"):
            return Response(status=401)
        return indexFiles(repo_path, Path("/"))
    return err404

if __name__ == '__main__':
    Logger.init(file=False)
    reload()
    Logger.info("Repo base path: "+repo_path)
    Logger.info("Protecting", protect)
    app.run(host='0.0.0.0', port=9800, debug=True)
 