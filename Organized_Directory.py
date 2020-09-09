try:
    from multiprocessing import Process
    from pathlib import Path
    from shutil import Error
    from lz4 import frame
    from datetime import datetime
    from argparse import ArgumentParser
    from shutil import rmtree, move
    from os import walk, scandir, remove
    from sys import exit
    import tarfile

except Exception:
    print(
        "can't import required Modules,"
        "probably because your python is too old"
        " or some Files are missing")
    exit(1)


def _main():
    print("Hello")
    # Commmandline Arg
    parser = ArgumentParser()
    parser.add_argument('-d', '--dir', help='Location of Directory to clean')
    parser.add_argument(
        '-p', '--pattern',
        help='name of the directorys default is : Y_%%B')
    parser.add_argument(
        '-m', '--max', help=(
            'Maximum Directorys in old'))
    parser.add_argument(
        '-c', '--cmax', help=(
            'Maximum compressed Files in old'))

    args = parser.parse_args()
    src = Path(args.dir)
    move_to_old(args, src)
    work_old_dirs(args, src)
    work_old_compressed_files(args, src)


def compress_dir(entry):
    dst_file = Path(entry.path + ".tar.lz4")
    if not dst_file.is_file():
        with open(entry.path + ".txt", 'w') as txt:
            for path, _subdirs, files in walk(entry.path):
                for name in files:
                    txt.write(path + name)
                    txt.write("\n")

        print("Compress: " + entry.name)
        lz4_file = frame.LZ4FrameFile(
            dst_file, mode='w',
            compression_level=frame.COMPRESSIONLEVEL_MIN,
            block_checksum=True
        )
        with tarfile.open(mode='w', fileobj=lz4_file) as tar_xz_file:
            tar_xz_file.add(entry.path)
        lz4_file.close()
    else:
        print(dst_file.__str__() + " already exist")
    print("Remove Directory: " + entry.path)
    rmtree(entry.path)


def compress_old_dirs(list_dirs_to_compress):
    list_p = list()
    for entry in list_dirs_to_compress:
        if entry.is_dir():
            list_p.append(
                Process(target=compress_dir, args=(entry,))
            )
            list_p[-1].start()
    for process in list_p:
        process.join()


def work_old_dirs(args, src):
    list_dirs = list()
    list_dirs_to_compress = list()
    max_dirs = int(args.max)
    with scandir(str(src) + '/old') as it:
        for entry in it:
            if entry.is_dir():
                list_dirs.append(entry)
    while len(list_dirs) > max_dirs:
        time_s = None
        item_s = None
        for item in list_dirs:
            item_time = datetime.fromtimestamp(
                item.stat().st_mtime)
            if time_s is None:
                time_s = item_time
                item_s = item
            elif item_time < time_s:
                time_s = item_time
                item_s = item
        try:
            list_dirs_to_compress.append(item_s)
            list_dirs.remove(item_s)
        except Exception as e:
            print(e)
            exit(1)

    compress_old_dirs(list_dirs_to_compress)


def work_old_compressed_files(args, src):
    list_files = list()
    max_files = int(args.cmax)
    with scandir(str(src) + '/old') as it:
        for entry in it:
            if entry.is_file() and "tar.xz" in entry.name:
                list_files.append(entry)

    while len(list_files) > max_files:
        time_s = None
        item_s = None
        for item in list_files:
            item_time = datetime.fromtimestamp(
                item.stat().st_mtime)
            if time_s is None:
                time_s = item_time
                item_s = item
            elif item_time < time_s:
                time_s = item_time
                item_s = item
        try:
            print("Removing: " + item_s.path)
            remove(item_s)
            txt = item_s.path[:item_s.path.find(".")] + ".txt"
            print("removing: " + txt)
            remove(txt)
            list_files.remove(item_s)
        except Exception as e:
            print(e)
            exit(1)


def move_to_old(args, src):
    if args.pattern:
        dst_pattern = args.pattern
    else:
        dst_pattern = "%Y_%B"
    dst = Path(
        str(src) + '/old/' + datetime.strftime(
            datetime.now(), dst_pattern))
    dst.mkdir(parents=True, exist_ok=True)
    for entry in scandir(str(src)):
        if entry.name != 'old':
            try:
                move(entry.path, dst)
                print('moved ' + entry.path)
            except Error as e:
                try:
                    remove(entry.path)
                    print('Error, removed ' + entry.path)
                    print(e)
                except Exception as e:
                    try:
                        rmtree(entry.path)
                        print('Error removed Dir ' + entry.path)
                        print(e)
                    except Exception as e:
                        print(e)


if __name__ == "__main__":
    _main()
