
import pathlib

from . import util


class BuildConfig(object):
    def __init__(self, qcc_cmd, qcc_flags, dat_expected_name, dat_final_name, cvar=None):
        self.__dict__.update(locals())


class QCModule(object):
    def __init__(self, name, path):
        self.name = name
        self.path = util.directory(path)
        self.log = util.logger(__name__, name)

    def build(self, build_info, module_config):
        use_cache = bool(build_info.cache_dir and build_info.cache_qc)
        build_dir = util.make_directory(pathlib.Path.cwd() / 'qcc' / module_config.dat_final_name)

        if use_cache:
            if self.name == 'menu':
                myhash = build_info.repo.qchash_menu.hexdigest()
            else:
                if self.name == 'client':
                    basehash = build_info.repo.qchash_menu
                else:
                    basehash = build_info.repo.qchash_common

                myhash = util.hash_path(self.path, hashobject=basehash.copy(), namefilter=util.namefilter_qcmodule)
                myhash = myhash.hexdigest()

            cache_dir = build_info.cache_dir / 'qc' / module_config.dat_final_name / myhash

            if cache_dir.is_dir():
                self.log.info('Using a cached version for %s (%r)', module_config.dat_final_name, str(cache_dir))
                util.copy_tree(cache_dir, build_dir)
                return build_dir

            cache_dir = util.make_directory(cache_dir)

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
            util.copy_tree(build_dir, cache_dir)

        return build_dir
