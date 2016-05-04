
import pathlib
import re
import io

from .compat import *

from . import util


class BuildConfig(object):
    def __init__(self, qcc_cmd, qcc_flags, dat_expected_name, dat_final_name, cvar=None):
        self.__dict__.update(locals())


class QCModule(object):
    def __init__(self, name, path):
        self.name = name
        self.path = util.directory(path)
        self.log = util.logger(__name__, name)

        self.needs_auto_header = False
        with (self.path / 'progs.src').open() as progsfile:
            for line in progsfile:
                if line.endswith('/rm_auto.qh'):
                    self.needs_auto_header = True
                    break

    def compute_hash(self, hash):
        p = self.path
        strip = lambda s: re.sub(r'\s*//.*|\s*$|^\s*', '', s)
        progspath = p / 'progs.src'
        include_re = re.compile(r'#include\s*[<"](.*?)[>"]')

        def hash_qc_file(path):
            includes = []
            hash.update(str(path).encode('utf-8'))

            with path.open('rb') as qcfile:
                for line in qcfile:
                    hash.update(line)
                    match = include_re.match(line.decode('utf-8'))
                    if match:
                        includes.append(match.group(1))

            for inc in filter(lambda i: i != 'rm_auto.qh', includes):
                hash_qc_file((path.parent / inc).resolve())

        with progspath.open() as progsfile:
            for line in filter(lambda l: l and not l.endswith('.dat'), map(lambda l: strip(l), progsfile)):
                hash_qc_file(util.file((progspath.parent / line).resolve()))

        return hash

    def build(self, build_info, module_config):
        use_cache = bool(build_info.cache_dir and build_info.cache_qc)
        build_dir = util.make_directory(pathlib.Path.cwd() / 'qcc' / module_config.dat_final_name)

        if use_cache:
            if self.name == 'menu':
                myhash = build_info.repo.qchash_menu.hexdigest()
            else:
                if self.name == 'client':
                    basehash = build_info.repo.qchash_menu.copy()
                else:
                    basehash = util.hash_constructor()

                myhash = self.compute_hash(basehash).hexdigest()

            cache_dir = build_info.cache_dir / 'qc' / module_config.dat_final_name / myhash

            if cache_dir.is_dir() and not build_info.force_rebuild:
                self.log.info('Using a cached version for %s (%r)', module_config.dat_final_name, str(cache_dir))
                util.copy_tree(cache_dir, build_dir)
                return build_dir

        self.log.info('Building %s from %r', module_config.dat_final_name, str(self.path))

        util.logged_subprocess(
            [module_config.qcc_cmd, '-src', str(self.path)] + module_config.qcc_flags,
            self.log,
            cwd=str(build_dir)
        )

        if module_config.dat_expected_name != module_config.dat_final_name:
            for fpath in build_dir.glob('*'):
                if fpath.stem == module_config.dat_expected_name:
                    fpath.rename(fpath.with_name('%s%s' % (module_config.dat_final_name, fpath.suffix)))

        if use_cache:
            cache_dir = util.make_directory(cache_dir)
            self.log.info('Caching %s for reuse (%r)', module_config.dat_final_name, str(cache_dir))
            util.copy_tree(build_dir, cache_dir)

        return build_dir
