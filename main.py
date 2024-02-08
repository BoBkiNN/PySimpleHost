from flask import Flask, Response, request, send_file, Request, redirect, url_for
import os, re, json, base64, time
import humanize
from watchdog.observers.polling import PollingObserver as Observer
import watchdog.events
from Path import Path
from config import Config
import Logger

CFG_FILE = os.getcwd()+os.sep+"config.json"
BROWSER_PATTERN = re.compile("Chrome|Mozilla|Safari|Opera")
DARK_THEME_STYLES = """<style>
    @media (prefers-color-scheme: dark) {
        body {
            background: #333;
            color: #FFF;
        }
        a:link {
            color: #59afff
        }
        a:visited {
            color: #7583ff
        }
    }
    </style>
    """
DEF_CFG = {
    "repo_path": os.getcwd()+os.sep+"repository",
    "user": "admin",
    "password": "password",
    "protect": ["put"], # All: ["download", "put", "browse"]
    "display": {
        "col1-spacing": 51,
        "col2-spacing": 20,
        "gnu-style-size": True,
        "display-mtime": True,
        "display-size": True,
        "auto-dark-theme": True
    },
    "watchdog": True
}
DEF_AUTH = "admin:password"

def load_cfg(return_fallback: bool, fallback: dict = {}) -> dict:
    if os.path.isfile(CFG_FILE):
        with open(CFG_FILE, "r") as f:
            Logger.info("Loading config")
            try:
                return json.loads(f.read())
            except:
                return fallback
    else:
        if return_fallback:
            return fallback
        save_cfg(DEF_CFG)
        return DEF_CFG

def save_cfg(data: dict):
    with open(CFG_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

repo_path = Path(DEF_CFG["repo_path"])
auth = base64.b64encode(DEF_AUTH.encode()).decode()
curr_cfg: dict = {}
config: Config = Config()

def reload(on_start: bool):
    global repo_path, auth, curr_cfg, config
    d = load_cfg(not on_start, curr_cfg)
    config[""] = d
    curr_cfg = d
    repo_path = d["repo_path"]
    if repo_path == None:
        repo_path = Path(DEF_CFG["repo_path"])
    else:
        repo_path = Path(repo_path)
    repo_path = repo_path.expand_user()
    user = d["user"]
    pw = d["password"]
    if user == None or pw == None:
        auth = base64.b64encode(DEF_AUTH.encode())
    else:
        auth = base64.b64encode(str.encode(user+":"+pw))
    auth = auth.decode()
    enable_watchdog: bool = config.get("watchdog", True)
    if not enable_watchdog:
        if watcher.is_alive():
            Logger.info("Stopping watchdog")
            watcher.stop()

class ConfigChangeHandler(watchdog.events.FileSystemEventHandler):
    def __init__(self) -> None:
        super().__init__()
    def on_modified(self, event: watchdog.events.FileSystemEvent):
        if not event.is_directory:
            self.on_config_change()
    
    def on_config_change(self):
        Logger.info("Detected config change, reloading")
        reload(False)

watcher = Observer()

def check_access(perm: str) -> bool:
    if perm in config.get("protect", ["put"]):
        h = request.headers.get("Authorization", None)
        if h == None:
            return False
        if h.startswith("Basic "):
            provided = h.removeprefix("Basic ")
            return auth == provided
        else: return False
    else:
        return True

app = Flask("PyMavenRepo")
err404 = Response(status=404)

def errc(code: int) -> Response:
    return Response(f"<!DOCTYPE html><html><head></head><body><h1>{code}</h1></body></html>", code)

err404c = errc(404)
err401c = Response(status=401, headers={"WWW-Authenticate": f"Basic realm=\"{app.import_name}\""})

def is_browser(r: Request):
    return BROWSER_PATTERN.findall(r.headers["User-Agent"]) != None

def download_file(path: Path) -> Response:
    if os.path.isfile(path.to_str()):
        return send_file(path.to_str())
    return err404c

def list_and_sort_files(directory):
    files = os.listdir(directory)
    # Separate directories and files
    directories = [d for d in files if os.path.isdir(os.path.join(directory, d))]
    files = [f for f in files if os.path.isfile(os.path.join(directory, f))]
    directories.sort()
    files.sort()
    return directories + files

def get_formatted_file_modify_time(file_path):
    if not config.get("show-mtime", True):
        return ""
    try:
        # Get the last modification time of the file
        modification_time = os.path.getmtime(file_path)

        # Convert the modification time to a struct_time
        time_struct = time.gmtime(modification_time)
        return time.strftime('%d-%b-%Y %H:%M', time_struct)
    except FileNotFoundError:
        return "-"

def get_file_size(file_path: str):
    if not config.get("show-size", True):
        return ""
    if os.path.isfile(file_path):
        size_in_bytes = os.path.getsize(file_path)
        if config.get("display.humanize-size", True):
            return humanize.naturalsize(size_in_bytes, True, config.get("display.gnu-style-size", True), "%.2f")
        else:
            return str(size_in_bytes)
    else:
        return "-"

def shift_text_right(strsize: int, text: str):
    spaces = max(1, strsize-len(text))
    return " "*spaces+text

def index_files(path: Path, relative: Path) -> Response:
    p = path.to_str()
    if not os.path.isdir(p):
        return err404c if not is_browser(request) else err404
    ls = list_and_sort_files(p)
    indexstr = relative.to_str().replace(os.sep, "/").removeprefix("/")
    if not indexstr.endswith("/") and len(indexstr) > 0:
        indexstr+="/"
    indexstr = "/"+indexstr
    if not is_browser(request):
        d = {"indexOf": indexstr}
        files = []
        for name in ls:
            file_path = path.resolve(name).to_str()
            if not os.path.exists(file_path): continue
            o = {"name": name, "path": indexstr+name}
            if config.get("show-mtime", True):
                mtime = os.path.getmtime(file_path)
                o["mtime"] = int(mtime*1000) # ms
            if os.path.isdir(file_path):
                o["dir"] = True
                files.append(o)
                continue
            if config.get("show-size", True):
                o["size"] = os.path.getsize(file_path)
            files.append(o)
        d["len"] = len(files) # type: ignore
        d["ls"] = files # type: ignore
        return Response(json.dumps(d), status=200, mimetype="application/json")
            
    empty = ""
    auto_dark_theme: bool = config.get("display.auto-dark-theme", True)
    html = f"<!DOCTYPE html><html><title>Index of {indexstr}</title><head>{DARK_THEME_STYLES if auto_dark_theme else empty}</head><body><h1>Index of {indexstr}</h1><hr><pre>"
    if path != repo_path:
        html += f"<a href=\"../\">../</a>"+"\n"
    for f in ls:
        fp = path.resolve(f).to_str()
        filesize = get_file_size(fp)
        mtime = get_formatted_file_modify_time(fp)
        sizestr = shift_text_right(config.get("display.col2-spacing", 20), filesize)
        if os.path.isdir(fp):
            href = f+"/"
        else:
            href = f
        mtimestr = " "*max(1, config.get("display.col1-spacing", 51)-len(href))+mtime
        metastr: str = mtimestr+sizestr
        html += f"<a href={href}>{href}</a>{metastr.rstrip()}\n"
    html += "</pre><hr></body></html>"
    return Response(html, 200, mimetype="text/html")


def put_file(fullPath: Path, r: Request) -> Response:
    if not config.get("enable-put", True):
        return err401c if is_browser(request) else Response(status=401)
    # print(len(r.data), len(r.files), r.files.to_dict())
    Logger.info("Uploading file "+fullPath)
    os.makedirs(fullPath.get_parent().to_str(), exist_ok=True)
    p = fullPath.to_str()
    if os.path.exists(p):
        mode = "wb"
    else:
        mode = "xb"
    with open(p, mode) as f:
        f.write(r.data)
    return Response(status=201)

@app.route('/<path:urlPath>', methods=["GET", "PUT"])
def main_route(urlPath: str):
    path: Path = repo_path.resolve(urlPath)
    browser = is_browser(request)
    if os.path.isdir(path.to_str()):
        if not check_access("index"):
            return err401c if browser else Response(status=401)
        # Logger.info(path)
        if not urlPath.endswith("/"):
            return redirect(url_for('main_route', urlPath=urlPath + '/'))
        return index_files(path, Path(urlPath))
    if request.method == "GET":
        if not check_access("get") and not browser:
            return err401c if browser else Response(status=401)
        return download_file(path)
    elif request.method == "PUT":
        if not check_access("put"):
            return err401c if browser else Response(status=401)
        return put_file(path, request)
    else:
        return Response(status=405)

@app.route("/")
def root():
    if not check_access("index"):
        return err401c if is_browser(request) else Response(status=401)
    return index_files(repo_path, Path("/"))
def start():
    Logger.init(file=False)
    reload(True)
    if config.get("watchdog", True):
        watcher.schedule(ConfigChangeHandler(), CFG_FILE)
        watcher.start()
        Logger.info("Tracking "+CFG_FILE+" updates:", watcher.is_alive())
    Logger.info("Base path: "+repo_path)
    Logger.info("Protecting", config.get("protect", ["put"]))
    return app

if __name__ == '__main__':
    start().run(host='0.0.0.0', port=9800, debug=True)
 