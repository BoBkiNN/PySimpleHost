from flask import Flask, Response, request, send_file, Request, redirect, url_for
import os, re, json, base64, time
import humanize
from typing import Union
from urllib.parse import quote
from watchdog.observers.polling import PollingObserver as Observer
import watchdog.events
from Path import Path
from config import Config
import Logger

CFG_FILE = os.path.join(os.getcwd(), "config.json")
BROWSER_PATTERN = re.compile("Chrome|Mozilla|Safari|Opera")
DARK_THEME_STYLES = """<style>
    @media (prefers-color-scheme: dark) {
        body {
            background: #131417;
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
    "user": "admin",
    "password": "password",
    "protect": ["put"], # All: ["get", "put", "index"]
    "show-mtime": True,
    "show-size": True,
    "display": {
        "col1-spacing": 51,
        "col2-spacing": 20,
        "humanize-size": True,
        "gnu-style-size": True,
        "auto-dark-theme": True
    },
    "watchdog": True
}
DEF_AUTH = "admin:password"

def load_cfg(return_fallback: bool, fallback: dict = dict()) -> dict:
    if os.path.isfile(CFG_FILE):
        with open(CFG_FILE, "r", encoding="utf-8") as f:
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
    with open(CFG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

auth = base64.b64encode(DEF_AUTH.encode()).decode()
curr_cfg: dict = dict()
config: Config = Config()
contents: dict[str, str] = dict()

def reload(on_start: bool):
    global auth, curr_cfg, config, contents
    d = load_cfg(not on_start, curr_cfg)
    config[""] = d
    curr_cfg = d
    user = d["user"]
    pw = d["password"]
    if user == None or pw == None:
        auth = base64.b64encode(DEF_AUTH.encode())
    else:
        auth = base64.b64encode(str.encode(user+":"+pw))
    auth = auth.decode()
    contents = config.get("contents", dict())
    if len(contents) > 0: Logger.info("Contents:")
    for k, v in contents.copy().items():
        contents.pop(k)
        rk = k.strip("/")
        rp = Path(v).expand_user().to_str()
        if os.path.isdir(rp):
            rp = rp.removesuffix(os.sep)+os.sep
        contents[rk]=rp
        Logger.info(f"  '{rk}' -> '{rp}'")
    contents = {key: contents[key] for key in sorted(contents.keys(), key=lambda x: len(x), reverse=True)}

    enable_watchdog: bool = config.get("watchdog", True)
    if not enable_watchdog:
        if WATCHER.is_alive():
            Logger.info("Stopping watchdog")
            WATCHER.stop()

class ConfigChangeHandler(watchdog.events.FileSystemEventHandler):
    def __init__(self) -> None:
        super().__init__()
    def on_modified(self, event: watchdog.events.FileSystemEvent):
        if not event.is_directory:
            self.on_config_change()
    
    def on_config_change(self):
        Logger.info("Detected config change, reloading")
        reload(False)

WATCHER = Observer()
APP = Flask("PySimpleHost")
ERR_401_C = Response(status=401, headers={"WWW-Authenticate": f"Basic realm=\"{APP.import_name}\""})
ERR_401 = Response(status=401)
ERR_404 = Response(status=404)

def check_access(perm: str) -> bool:
    protect = config.get("protect", ["put"])
    if perm in protect or "all" in protect:
        h = request.headers.get("Authorization", "")
        arg = request.args.get("auth", None, type=str)
        if h.startswith("Basic "):
            provided = h.removeprefix("Basic ")
            return auth == provided
        elif arg != None:
            sarg: str = arg
            provided = base64.b64encode(sarg.encode()).decode()
            return auth == provided
        else: return False
    else:
        return True

def errc(code: int) -> Response:
    return Response(f"<!DOCTYPE html><html><head>{DARK_THEME_STYLES if config.get('display.auto-dark-theme', True) else ''}</head><body><h1>{code}</h1></body></html>", code)

def is_browser(r: Request):
    matches = BROWSER_PATTERN.findall(r.headers.get("User-Agent", ""))
    return matches != None and len(matches) > 0

def download_file(path: Path) -> Response:
    if os.path.isfile(path.to_str()):
        return send_file(path.to_str())
    return errc(404) if is_browser(request) else ERR_404

def list_and_sort_files(directory):
    files = os.listdir(directory)
    # Separate directories and files
    directories = [d for d in files if os.path.isdir(os.path.join(directory, d))]
    files = [f for f in files if os.path.isfile(os.path.join(directory, f))]
    directories.sort()
    files.sort()
    directories.extend(files)
    return directories

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

def index_files(folder: Path, base: Path, relative: str) -> Response:
    p = folder.to_str()
    if not os.path.isdir(p):
        return errc(404) if not is_browser(request) else ERR_404
    ls = list_and_sort_files(p)
    indexstr = relative.replace(os.sep, "/").removeprefix("/")
    if not indexstr.endswith("/") and len(indexstr) > 0:
        indexstr+="/"
    indexstr = "/"+indexstr
    if not is_browser(request):
        d = {"indexOf": indexstr}
        files = []
        for name in ls:
            file_path = folder.resolve(name).to_str()
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
    
    auto_dark_theme: bool = config.get("display.auto-dark-theme", True)
    html = f"<!DOCTYPE html><html><head><title>Index of {indexstr}</title>{DARK_THEME_STYLES if auto_dark_theme else ''}</head><body><h1>Index of {indexstr}</h1><hr><pre>"
    # Logger.info(base, folder)
    if base != folder:
        html += f"<a href=\"../\">../</a>"+"\n"
    for f in ls:
        fp = folder.resolve(f).to_str()
        filesize = get_file_size(fp)
        mtime = get_formatted_file_modify_time(fp)
        sizestr = shift_text_right(config.get("display.col2-spacing", 20), filesize)
        if os.path.isdir(fp):
            href = f+"/"
        else:
            href = f
        mtimestr = " "*max(1, config.get("display.col1-spacing", 51)-len(href))+mtime
        metastr: str = mtimestr+sizestr
        html += f"<a href={quote(href)}>{href}</a>{metastr.rstrip()}\n"
    html += "</pre><hr></body></html>"
    return Response(html, 200, mimetype="text/html")


def put_file(fullPath: Path, r: Request) -> Response:
    if not config.get("enable-put", True):
        return ERR_401_C if is_browser(request) else ERR_401
    # print(len(r.data), len(r.files), r.files.to_dict())
    Logger.info("Uploading file "+fullPath)
    os.makedirs(fullPath.get_parent().to_str(), exist_ok=True)
    p = fullPath.to_str()
    with open(p, "wb" if os.path.exists(p) else "xb", encoding="utf-8") as f:
        f.write(r.data)
    return Response(status=201)

def process_fs(base: Path, relative: Path, full_path: str):
    path: Path = base.resolve(relative)
    browser = is_browser(request)
    if os.path.isdir(path.to_str()):
        if not check_access("index"):
            return ERR_401_C if browser else ERR_401
        # Logger.info(path)
        if not full_path.endswith("/"):
            return redirect(url_for('main_route', url_path=full_path + '/'))
        return index_files(path, base, relative.to_str().removeprefix("."))
    if request.method == "GET":
        if not check_access("get"):
            return ERR_401_C if browser else ERR_401
        return download_file(path)
    elif request.method == "PUT":
        if not check_access("put"):
            return ERR_401_C if browser else ERR_401
        return put_file(path, request)
    else:
        return Response(status=405)

def parse_content_dir(path: str) -> Union[tuple[Path, Path], None]: # [base, relative] or 404
    """Get base and relative or None if not found"""
    for k, v in contents.items():
        if path.startswith(k):
            rel = path.removeprefix(k).removeprefix("/")
            return Path(v), Path(rel)
    return None

def main_end(url_path: str):
    redirs: dict[str, str] = config.get("redirect-flow", dict())
    for k, v in redirs.items():
        if url_path == k:
            # Logger.info(f"Redirecting flow from '{k}' to '{v}'")
            url_path = v
    content_dir = parse_content_dir(url_path)
    # Logger.info("Content:", content_dir)
    if content_dir == None:
        return errc(404) if is_browser(request) else ERR_404
    base, relative = content_dir
    return process_fs(base, relative, request.path)

@APP.route('/<path:url_path>', methods=["GET", "PUT"])
def main_route(url_path: str):
    return main_end(url_path)

@APP.route("/", methods=["GET", "PUT"])
def root():
    return main_end("")

def start():
    Logger.init(file=False)
    reload(True)
    if config.get("watchdog", True):
        WATCHER.schedule(ConfigChangeHandler(), CFG_FILE)
        WATCHER.start()
        Logger.info("Tracking "+CFG_FILE+" updates:", WATCHER.is_alive())
    Logger.info("Protecting", config.get("protect", ["put"]))
    return APP

if __name__ == '__main__':
    start().run(host=config.get("host", "0.0.0.0"), port=config.get("port", 9800), debug=True)
 