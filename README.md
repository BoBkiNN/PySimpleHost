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
        "put" // list of "put", "download", "browse"
    ]
}
```

### Running:
* waitress: `python -m waitress --call --listen *:9800 main:start`
* not production: `python main.py`