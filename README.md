## Simple python flask server for hosting folder contents

### Features:
* Basic auth (username and password)
* Uploading and downloading files
* HTML view of repo (with dark theme)

### Config explanation:
```json5
{
    "user": "admin", // username 
    "password": "test123", // password
    "protect": [ // what features are protected using password. Defaults to ["put"]
        "put" // list of "put", "get", "index", "all"
    ],
    "show-mtime": true, // send file modify time in index?
    "show-size": true, // send file size in index?
    "display": { // settings of web index page
        "col1-spacing": 51, // size of first column
        "col2-spacing": 20, // size of second column
        "humanize-size": true, // if false, writes size in bytes
        "gnu-style-size": true, // if true, writes B, KB, MB and etc, else Bytes, KiB, MiB and etc
        "auto-dark-theme": true // if true, css for auto dark theme is added
    },
    "contents": {
        "": "~/www",
        "repo":"~/.m2/repository/"
    },
    "redirect-flow": { // where to omit content
        "": "index.html"
    },
    "watchdog": true // should we track changes in config.json?
}
```

### Protect values description:
* `put` - require auth when uploading files
* `get` - require auth when getting files
* `index` - require auth when accesing list of files
* `all` - combine of upper three values

### Installing
1. Clone repository `git clone https://github.com/BoBkiNN/SimpleRepoHost`
2. Install python >3.9
3. Install required modules: `python -m pip install -r requirements.txt`
4. Configure `config.json` inside cloned repository

### Running:
* waitress: 
    1. Install `waitress` module: `python -m pip install waitress`
    2. `python -m waitress --call --listen *:9800 main:start`
* not production: `python main.py`
