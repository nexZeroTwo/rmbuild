
import pathlib
import gzip
import functools

from .compat import *

from . import util

log = util.logger(__name__)

INDEX_FILENAME = '.rmbuild_index'


def build_index(path):
    path = util.directory(path)
    index = []

    def recurse(path):
        for fpath in path.iterdir():
            if fpath.is_file() or fpath.is_symlink():
                index.append(fpath)
            elif fpath.is_dir():
                recurse(fpath)

    recurse(path)
    index = sorted(map(lambda p: p.relative_to(path), index))
    return index


def open_index(path, mode):
    return gzip.open(str(path / INDEX_FILENAME), mode)


def write_index(index, path):
    path = util.directory(path)

    with open_index(path, 'wb') as ifile:
        for p in index:
            ifile.write(('%s\n' % str(p)).encode('utf-8'))


def read_index(path):
    path = util.directory(path)

    try:
        with open_index(path, 'rb') as ifile:
            paths = ifile.read().decode('utf-8').strip().split('\n')
    except FileNotFoundError:
        return []

    return sorted(map(lambda p: pathlib.Path(p), paths))


def index_directories(index):
    dirs = set(filter(lambda p: str(p) != '.', map(lambda p: p.parent, index)))

    for d in tuple(dirs):
        while True:
            d = d.parent
            if str(d) == '.':
                break
            dirs.add(d)

    return sorted(dirs, reverse=True)


def remove_old_files(path):
    path = util.directory(path)
    index = read_index(path)

    for p in index:
        p = path / p
        log.debug("Removing %r", str(p))

        with util.suppress_logged(log):
            p.unlink()

    for d in index_directories(index):
        d = path / d
        with util.suppress_logged(log):
            d.rmdir()
            log.debug('Removed empty directory %r', str(d))


def copy_by_index(index, src, dst, link=False):
    src = util.directory(src).resolve()
    dst = util.directory(dst).resolve()

    for d in index_directories(index):
        util.make_directory(dst / d)

    for f in index:
        if link:
            (dst / f).symlink_to(src / f)
        else:
            util.copy(src / f, dst / f)


link_by_index = functools.partial(copy_by_index, link=True)


def install(build_info, path, link=False, pathfilter=None):
    if pathfilter is None:
        pathfilter = lambda p: True
    elif isinstance(pathfilter, str):
        pathfilter = util.pathfilter_pattern(pathfilter)
    elif not callable(pathfilter):
        raise ValueError('pathfilter must be a string or callable, got %r' % pathfilter)

    log.info("Installing to %r (%s)", str(path), 'link' if link else 'copy')

    path = util.directory(path)
    remove_old_files(path)
    index = list(filter(pathfilter, build_index(build_info.output_dir)))
    write_index(index, path)
    copy_by_index(index, build_info.output_dir, path, link=link)
