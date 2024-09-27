# r2 (WIP)

# [Moved to SourceHut](https://git.sr.ht/~jackiejude/r2)

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

- better handling of missing files (see issue 1)
- prevent collision in filename when using quick add and regular add

## Future commands

```bash

r2 --list

r2 --list-backups file

# basic dotfiles management
r2 --link vimrc ~/.vimrc # the link is to a version of vimrc in .r2/store

# scripts
r2 --add-bin foo.py # adds foo.py to PATH
```
