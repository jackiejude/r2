#!/usr/bin/env python3

import os
import json
import shutil
import logging
import hashlib
import argparse
import datetime

HOME = os.path.expanduser('~')
R2DIR = os.path.join(HOME, ".r2")
STORE = os.path.join(R2DIR, "store")
DEFS = os.path.join(R2DIR, "defs.json")

log_format = "%(levelname)s [%(asctime)s] - %(message)s"
logging.basicConfig(filename='r2.log', encoding='utf-8', level=logging.ERROR, format=log_format)
logger = logging.getLogger()
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(logging.Formatter(log_format))
logger.addHandler(console_handler)

def mkdir(d):
    if not os.path.exists(d):
        os.mkdir(d)

def file_append(filename, contents):
    f = open(filename, "a")
    f.write(contents)
    f.close()

def file_overwrite(filename, contents):
    f = open(filename, "w")
    f.write(contents)
    f.close()

def file_read(filename):
    f = open(filename, "r")
    return f.read()

def hash_file(filename):
    BLOCKSIZE = 65536
    hasher = hashlib.sha1()
    with open(filename, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()

def handle_error(
        error_message: str,
        showLevel = logging.error,
        fatal: bool = False,
        errorCode: int = 1) -> None:
    showLevel(error_message)
    if fatal:
        exit(errorCode)

def build_generation(defs: dict) -> dict:
    for i in defs:
        path = defs[i]['path']
        hash = hash_file(path)
        new = int(defs[i]['latest']) + 1
        defs[i]['latest'] = new
        defs[i]['generations'].update({new: hash})
        store_location = os.path.join(STORE, hash)
        if not os.path.exists(store_location):
            shutil.copyfile(path, store_location)
    return defs

def get_default_def(name: str, path: str) -> dict:
    return {
        name: {
            "path": path,
            "latest": 0,
            "generations": {}
        }
    }

def init() -> None:
    mkdir(R2DIR)
    mkdir(STORE)
    file_overwrite(DEFS, json.dumps(get_default_def("defs", DEFS), indent=4))
    add_file("defs", DEFS)

def add_file(name: str, path: str) -> None:
    if not os.path.exists(path):
        handle_error("no such path " + path, fatal = True)
    if not os.path.exists(DEFS):
        handle_error("defs not found", fatal = True)
    defs = json.loads(file_read(DEFS))
    if not name in defs.keys():
        defs.update(get_default_def(name, path))
    defs = build_generation(defs)
    file_overwrite(DEFS, json.dumps(defs, indent=4))

def get_latest_gen(filename: str) -> str:
    defs = json.loads(file_read(DEFS))
    if not filename in defs.keys():
        handle_error("file does not exist " + filename, fatal = True)
    return defs[filename]['latest']

def get_file_at_gen(filename: str, generation: int, defs: dict) -> str:
    return os.path.join(STORE, defs[filename]['generations'][str(generation)])

def diff(filename: str, generation: int) -> bool:
    defs = json.loads(file_read(DEFS))
    if not filename in defs.keys():
        handle_error("file does not exist :" + filename, fatal = True)
    store_hash = os.path.basename(get_file_at_gen(filename, generation, defs))
    return hash_file(defs[filename]['path']) == store_hash

def restore(filename: str, generation: int, backup_first: bool = True) -> str:
    defs = json.loads(file_read(DEFS))
    path = defs[filename]['path']
    if backup_first:
        add_file(filename, path)
    shutil.copyfile(get_file_at_gen(filename, generation, defs), path)
    return "Restored file " + filename + " from backup " + str(generation)

def multi_arg(arg_list):
    amount = len(arg_list)
    filename = arg_list[0]
    if amount == 1:
        gen = get_latest_gen(filename)
    elif amount == 2:
        try:
            gen = int(arg_list[1])
        except ValueError:
            handle_error(error_message = "Generation must be an integer", fatal = True)
    elif amount > 2:
        handle_error(error_message = "Too many arguments", fatal = True)
    return (filename, gen)


def main() -> None:
    parser = argparse.ArgumentParser(
        description = "",
        epilog = ""
    )

    parser.add_argument('--init', action='store_true', help='Setup r2')
    parser.add_argument('-a', '--add', nargs = 2, type = str, default = '',
                        metavar = ('<name>', '<path>'), help = "Add file to r2")
    parser.add_argument('-q', '--quick-add', nargs = 1, type = str, default = '',
                        metavar = ('<file>'), help = "quick add file")
    parser.add_argument('-d', '--diff', nargs = '+', metavar = '', help = '<file> <generation> (default = latest)')
    parser.add_argument('-r', '--restore', nargs = '+', metavar = '', help = '<file> <generation> (default = latest)')
    parser.add_argument('-n', '--no_backup-first', action = 'store_false',
                        help = "backup before overwriting file with restore")

    args = parser.parse_args()

    if args.init:
        init()
        exit()
    elif args.add != '':
        add_file(args.add[0], args.add[1])
    elif args.quick_add != '':
        add_file(args.quick_add[0], os.path.join(os.getcwd(), args.quick_add[0]))
    elif args.diff != None:
        filename, gen = multi_arg(args.diff)
        if diff(filename, gen):
            print(filename, "matches backed up version", gen)
        else:
            print(filename, "differs from backed up version", gen)
    
    elif args.restore != None:
        filename, gen = multi_arg(args.restore)
        print(restore(filename, gen, args.no_backup_first))

    else:
        print("try --help")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\nexit')
        exit()
