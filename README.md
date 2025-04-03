# r2 (WIP)


## Usage

```bash
-a, --add <name> <path>
                    Add file to r2
-q, --quick-add <file>
                    Use filename as name
-d, --diff  [ ...]    <file> <generation> (default = latest)
-r, --restore  [ ...]
                    <file> <generation> (default = latest)
-n, --no-backup-first
                    Don't backup before overwriting file with restore
-l, --list-files      List backed up files
--remove <file>       Remove file from r2
--gc                  Run garbage collection
--history <file>      List history of a file
--prune [<file>]      Prune old generations of a file or all files
--status              Show status of all files
--link <file> <target>
                    Link a file to a target location
--install <file>      Install a file to ~/.r2/bin
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
- --update command (update an already added file)
- --update-all
- multiple storage locations
- directory support
- store only X latest versions of a file
- export history of a file
