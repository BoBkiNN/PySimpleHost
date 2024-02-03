## Simple python flask server for hosting maven repository

### Features:
* Basic auth (username and password)
* Uploading and downloading files
* HTML view of repo (with dark theme)

### Config explanation:
```json
{
    "repo_path": "D:\\repository", // path where files are located
    "user": "admin", // username 
    "password": "test123", // password
    "protect": [ // what features are protected using password. Defaults to ["put"]
        "put" // list of "put", "get", "download", "browse"
    ],
    "display": { // settings of web index page
        "col1-spacing": 51, // size of first column
        "col2-spacing": 20, // size of second column
        "humanize-size": true, // if false, writes size in bytes
        "gnu-style-size": true, // if true, writes B, KB, MB and etc, else Bytes, KiB, MiB and etc
        "display-mtime": true, // if true, displays file modify time
        "display-size": true, // if true, displays file size
        "auto-dark-theme": false // if true, css for auto dark theme is added
    },
    "watchdog": true // should we track changes in config.json?
}
```

### Protect values description:
* `put` - require auth when uploading files
* `get` - require auth when getting files outside browser
* `download` - require auth when getting files in browser
* `browse` - require auth when accesing list of files

### Running:
* waitress: `python -m waitress --call --listen *:9800 main:start`
* not production: `python main.py`