# r2 (WIP)


## Usage

```bash
$ r2 --init

$ r2 --add name path # backup file

$ r2 -q file # quick add (uses filename as name)

$ r2 -d file # check if file differs from backup

$ r2 -r file 1 # restore file from backup
```

## How it stores data

files are listed in `~/.r2/defs.json:`
```json
"test": {
    "path": "/tmp/test",
    "latest": 1,
    "generations": {
        "1": "4e1243bd22c66e76c2ba9eddc1f91394e57f9f83"
    }
}
```

```bash
$ cat ~/.r2/store/4e1243bd22c66e76c2ba9eddc1f91394e57f9f83 
test
```

## TODO

- [better handling of missing files](https://github.com/jackiejude/r2/issues/1)
- --update command (update an already added files)
- --update-all
- multiple storage locations
- directory support
- store only X latest versions of a file
- export history of a file
