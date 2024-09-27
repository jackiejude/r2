#!/usr/bin/env python3

import sys
import json
import shutil
import logging
import hashlib
import argparse
from typing import List, Dict, Tuple, Set
from pathlib import Path

HOME = Path.home()
R2DIR = HOME / ".r2"
STORE = R2DIR / "store"
DEFS = R2DIR / "defs.json"
BIN = R2DIR / "bin"

log_format = "%(levelname)s [%(asctime)s] - %(message)s"
logging.basicConfig(filename='r2.log', encoding='utf-8', level=logging.INFO, format=log_format)
logger = logging.getLogger()
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(log_format))
logger.addHandler(console_handler)

def mkdir(d: Path) -> None:
    d.mkdir(parents=True, exist_ok=True)

def file_append(filename: Path, contents: str) -> None:
    with open(filename, "a") as f:
        f.write(contents)

def file_overwrite(filename: Path, contents: str) -> None:
    with open(filename, "w") as f:
        f.write(contents)

def file_read(filename: Path) -> str:
    with open(filename, "r") as f:
        return f.read()

def hash_file(filename: Path) -> str:
    hasher = hashlib.sha256()
    block_size = 65536
    with open(filename, 'rb') as file:
        for chunk in iter(lambda: file.read(block_size), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def handle_error(
        error_message: str,
        show_level: int = logging.ERROR,
        fatal: bool = False,
        error_code: int = 1) -> None:
    logger.log(show_level, error_message)
    if fatal:
        sys.exit(error_code)

def build_generation(defs: Dict[str, Dict]) -> Dict[str, Dict]:
    for name, file_info in defs.items():
        path = Path(file_info['path'])
        if not path.exists():
            handle_error(f"File not found: {path}", show_level=logging.WARNING)
            continue
        hash_value = hash_file(path)
        new_gen = int(file_info['latest']) + 1
        file_info['latest'] = new_gen
        file_info['generations'][new_gen] = hash_value
        store_location = STORE / hash_value
        if not store_location.exists():
            shutil.copy2(path, store_location)
    return defs

def get_default_def(name: str, path: str) -> Dict[str, Dict]:
    return {
        name: {
            "path": str(path),
            "latest": 0,
            "generations": {}
        }
    }

def init() -> None:
    mkdir(R2DIR)
    mkdir(STORE)
    mkdir(BIN)
    file_overwrite(DEFS, json.dumps(get_default_def("defs", DEFS), indent=4))
    add_file("defs", DEFS)

def add_file(name: str, path: Path) -> None:
    path = Path(path).resolve()
    if not path.exists():
        handle_error(f"No such path: {path}", fatal=True)
    if not DEFS.exists():
        handle_error("defs not found", fatal=True)
    defs = json.loads(file_read(DEFS))
    if name not in defs:
        defs.update(get_default_def(name, path))
    defs = build_generation(defs)
    file_overwrite(DEFS, json.dumps(defs, indent=4))

def get_latest_gen(filename: str) -> int:
    defs = json.loads(file_read(DEFS))
    if filename not in defs:
        handle_error(f"File does not exist: {filename}", fatal=True)
    return defs[filename]['latest']

def get_file_at_gen(filename: str, generation: int, defs: Dict[str, Dict]) -> Path:
    return STORE / defs[filename]['generations'][str(generation)]

def diff(filename: str, generation: int) -> bool:
    defs = json.loads(file_read(DEFS))
    if filename not in defs:
        handle_error(f"File does not exist: {filename}", fatal=True)
    store_hash = get_file_at_gen(filename, generation, defs).name
    return hash_file(Path(defs[filename]['path'])) == store_hash

def restore(filename: str, generation: int, backup_first: bool = True) -> str:
    defs = json.loads(file_read(DEFS))
    path = Path(defs[filename]['path'])
    if backup_first:
        add_file(filename, path)
    shutil.copy2(get_file_at_gen(filename, generation, defs), path)
    return f"Restored file {filename} from backup {generation}"

def list_files() -> str:
    defs = json.loads(file_read(DEFS))
    if not defs:
        return "No files in the backup system."

    name_width = max(len(name) for name in defs.keys())
    path_width = max(len(info['path']) for info in defs.values())

    header = f"| {'Filename':<{name_width}} | {'Path':<{path_width}} |"
    separator = f"|{'-' * (name_width + 2)}|{'-' * (path_width + 2)}|"

    file_list = [header, separator]
    for name, info in defs.items():
        file_list.append(f"| {name:<{name_width}} | {info['path']:<{path_width}} |")

    return "\n".join(file_list)

def multi_arg(arg_list: List[str]) -> Tuple[str, int]:
    amount = len(arg_list)
    filename = arg_list[0]
    if amount == 1:
        gen = get_latest_gen(filename)
    elif amount == 2:
        try:
            gen = int(arg_list[1])
        except ValueError:
            handle_error("Generation must be an integer", fatal=True)
    else:
        handle_error("Too many arguments", fatal=True)
    return (filename, gen)

def delete_file(filename: str) -> str:
    defs = json.loads(file_read(DEFS))
    if filename not in defs:
        handle_error(f"File does not exist: {filename}", fatal=True)
    del defs[filename]
    file_overwrite(DEFS, json.dumps(defs, indent=4))
    print(garbage_collect())
    return f"Deleted {filename} from r2 backup system"

def garbage_collect() -> str:
    defs = json.loads(file_read(DEFS))
    valid_hashes: Set[str] = set()
    for file_info in defs.values():
        valid_hashes.update(file_info['generations'].values())

    deleted_count = 0
    for file in STORE.iterdir():
        if file.name not in valid_hashes:
            file.unlink()
            deleted_count += 1

    return f"Garbage collection complete. Deleted {deleted_count} unused file(s)."

def quick_add(filename: str) -> str:
    path = Path.cwd() / filename
    if not path.exists():
        handle_error(f"No such file: {path}", fatal=True)

    defs = json.loads(file_read(DEFS))
    base_name = path.stem
    extension = path.suffix
    new_name = base_name
    counter = 1

    while new_name in defs:
        new_name = f"{base_name}-{counter}{extension}"
        counter += 1

    add_file(new_name, path)
    return f"Added file {path} as {new_name}"

def list_file_history(filename: str) -> str:
    defs = json.loads(file_read(DEFS))
    if filename not in defs:
        handle_error(f"File does not exist: {filename}", fatal=True)

    file_info = defs[filename]
    history = [f"File: {filename}", f"Path: {file_info['path']}", ""]
    history.append("| Generation | Hash |")
    history.append("|------------|------|")

    for gen, hash_value in sorted(file_info['generations'].items(), key=lambda x: int(x[0])):
        history.append(f"| {gen:^10} | {hash_value} |")

    return "\n".join(history)

def prune(filename: str, all_files: bool = False) -> str:
    defs = json.loads(file_read(DEFS))
    if all_files:
        files_to_prune = list(defs.keys())
    else:
        if filename not in defs:
            handle_error(f"File does not exist: {filename}", fatal=True)
        files_to_prune = [filename]

    pruned_count = 0
    for file in files_to_prune:
        file_info = defs[file]
        latest_gen = str(file_info['latest'])
        latest_hash = file_info['generations'][latest_gen]
        old_generations = [gen for gen in file_info['generations'] if gen != latest_gen]

        for gen in old_generations:
            del file_info['generations'][gen]
            pruned_count += 1

        file_info['generations'] = {latest_gen: latest_hash}

    file_overwrite(DEFS, json.dumps(defs, indent=4))
    print(garbage_collect())
    return f"Pruned {pruned_count} old generation(s)."

def status() -> str:
    defs = json.loads(file_read(DEFS))
    if not defs:
        return "No files in the backup system."

    name_width = max(len(name) for name in defs.keys())
    status_width = len("Source File Missing")

    header = f"| {'Filename':<{name_width}} | {'Status':<{status_width}} |"
    separator = f"|{'-' * (name_width + 2)}|{'-' * (status_width + 2)}|"

    status_list = [header, separator]
    for name, file_info in defs.items():
        path = Path(file_info['path'])
        if not path.exists():
            status = "Source File Missing"
        else:
            current_hash = hash_file(path)
            latest_gen = str(file_info['latest'])
            latest_hash = file_info['generations'][latest_gen]    
            status = "Not Changed" if current_hash == latest_hash else "Changed"
        status_list.append(f"| {name:<{name_width}} | {status:<{status_width}} |")

    return "\n".join(status_list)

def link_file(filename: str, target_path: str) -> str:
    defs = json.loads(file_read(DEFS))
    if filename not in defs:
        handle_error(f"File does not exist in r2: {filename}", fatal=True)

    target = Path(target_path).expanduser().resolve()
    if target.exists():
        handle_error(f"Target path already exists: {target}", fatal=True)

    latest_gen = str(defs[filename]['latest'])
    source = get_file_at_gen(filename, int(latest_gen), defs)

    target.symlink_to(source)
    return f"Linked {filename} to {target}"

def install_file(filename: str) -> str:
    defs = json.loads(file_read(DEFS))
    if filename not in defs:
        handle_error(f"File does not exist in r2: {filename}", fatal=True)

    latest_gen = str(defs[filename]['latest'])
    source = get_file_at_gen(filename, int(latest_gen), defs)
    target = BIN / filename

    if target.exists():
        handle_error(f"File already exists in bin: {target}", fatal=True)

    target.symlink_to(source)
    target.chmod(target.stat().st_mode | 0o111)  # Make executable
    return f"Installed {filename} to {target}"

def main() -> None:
    parser = argparse.ArgumentParser(description="r2 backup system", epilog="")

    parser.add_argument('--init', action='store_true', help='Setup r2')
    parser.add_argument('-a', '--add', nargs=2, type=str, metavar=('<name>', '<path>'), help="Add file to r2")
    parser.add_argument('-q', '--quick-add', nargs=1, type=str, metavar=('<file>'), help="Quick add file")
    parser.add_argument('-d', '--diff', nargs='+', metavar='', help='<file> <generation> (default = latest)')
    parser.add_argument('-r', '--restore', nargs='+', metavar='', help='<file> <generation> (default = latest)')
    parser.add_argument('-n', '--no-backup-first', action='store_false', help="Don't backup before overwriting file with restore")
    parser.add_argument('-l', '--list-files', action='store_true', help="List backed up files")
    parser.add_argument('--delete', nargs=1, type=str, metavar='<file>', help="Delete file from r2 backup system")
    parser.add_argument('--gc', action='store_true', help="Run garbage collection")
    parser.add_argument('--history', nargs=1, type=str, metavar='<file>', help="List history of a file")
    parser.add_argument('--prune', nargs='?', const='all', metavar='<file>', help="Prune old generations of a file or all files")
    parser.add_argument('--status', action='store_true', help="Show status of all files")
    parser.add_argument('--link', nargs=2, type=str, metavar=('<file>', '<target>'), help="Link a file to a target location")
    parser.add_argument('--install', nargs=1, type=str, metavar='<file>', help="Install a file to .r2/bin")

    args = parser.parse_args()

    if args.init:
        init()
    elif args.add:
        add_file(args.add[0], args.add[1])
    elif args.quick_add:
        print(quick_add(args.quick_add[0]))
    elif args.list_files:
        print(list_files())
    elif args.diff:
        filename, gen = multi_arg(args.diff)
        if diff(filename, gen):
            print(f"{filename} matches backed up version {gen}")
        else:
            print(f"{filename} differs from backed up version {gen}")
    elif args.restore:
        filename, gen = multi_arg(args.restore)
        print(restore(filename, gen, args.no_backup_first))
    elif args.delete:
        print(delete_file(args.delete[0]))
    elif args.gc:
        print(garbage_collect())
    elif args.history:
        print(list_file_history(args.history[0]))
    elif args.prune:
        if args.prune == 'all':
            print(prune('', all_files=True))
        else:
            print(prune(args.prune))
    elif args.status:
        print(status())
    elif args.link:
        print(link_file(args.link[0], args.link[1]))
    elif args.install:
        print(install_file(args.install[0]))
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\nexit')
        sys.exit()
