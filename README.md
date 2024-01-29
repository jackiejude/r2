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

- prevent collision in filename
- list files
- list history of individual file
- multiple storage locations
- all existing commands, but recursively on directories
- rm - remove from defs
- purge - remove all instances of file from store
    - how should past generations handle it?
- garbage collection
- store only latest x versions of thing
- status (all files diff)
- export history of file
- target symlinked outside

## Future commands

```bash

r2 --list

r2 --list-backups file

# basic dotfiles management
r2 --link vimrc ~/.vimrc # the link is to a version of vimrc in .r2/store

# scripts
r2 --add-bin foo.py # adds foo.py to PATH
```
