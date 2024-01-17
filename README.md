## Simple python flask server for hosting maven repository

### Features:
* Basic auth (username and password)
* Uploading and downloading files
* HTML view of repo

### Config explanation:
```json
{
    "repo_path": "D:\\repository", // path where files are located
    "user": "admin", // username 
    "password": "test123", // password
    "protect": [ // what features are protected using password. Defaults to ["put"]
        "put" // list of "put", "get", "download", "browse"
    ]
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