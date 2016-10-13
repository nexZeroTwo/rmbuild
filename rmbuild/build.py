
import datetime
import shlex
import shutil
import functools
import multiprocessing

from concurrent import futures

from .compat import *

from . import util
from . import package
from . import qcmodule
from . import errors
from . import install

log = util.logger(__name__)


class BuildInfo(object):
    def __init__(self, repo,
                    qcc_cmd='rmqcc',
                    output_dir=None,
                    qcc_flags=None,
                    comment="custom build",
                    suffix=None,
                    autocvars='compatible',
                    threads=None,
                    extra_packages=(),
                    link_pk3dirs=False,
                    compress_gfx=True,
                    compress_gfx_quality=85,
                    compress_gfx_all=True,
                    cache_dir=None,
                    cache_qc=True,
                    cache_pkg=True,
                    force_rebuild=False,
                    hooks=None,
                    server_package='pk3',
                ):

        if hooks is None:
            hooks = {}

        if threads is None:
            threads = multiprocessing.cpu_count() * 5

        qcc_cmd = str(qcc_cmd)

        self.__dict__.update(locals())

        self.date = datetime.datetime.now()
        self.date_string = self.date.strftime('%F %T %Z').strip()

        if suffix is None:
            suffix = repo.rm_branch
            if suffix == 'master':
                suffix = ''

        self.name = "RocketMinsta"

        if suffix:
            self.name += '-' + suffix

        self.suffix = suffix
        self.version = repo.rm_version

        if cache_dir is not None:
            self.cache_dir = util.make_directory(cache_dir).resolve()
        else:
            self.cache_dir = None

        self.temp_dir = util.temp_directory()

        if output_dir is None:
            output_dir = self.temp_dir / 'build'

        self.output_dir = util.make_directory(output_dir).resolve()

        if qcc_flags is None:
            qcc_flags = []
        elif isinstance(qcc_flags, str):
            qcc_flags = shlex.split(qcc_flags)

        self.qcc_flags = qcc_flags

        self.qc_defs = self.get_qc_defs()
        self.qc_module_config = {}
        self.configure_qc_modules()

        self.built_qc_modules = {}
        self.built_packages = []

        self.install = functools.partial(install.install, self)

        self.failed = False
        self.futures = []
        self.tasks = {}
        self.executor = futures.ThreadPoolExecutor(self.threads)

    def configure_qc_module(self, name, *args, **kwargs):
        if name in self.qc_module_config:
            cfgs = self.qc_module_config[name]
        else:
            cfgs = []
            self.qc_module_config[name] = cfgs

        cfgs.append(qcmodule.BuildConfig(*args, **kwargs))

    def configure_qc_modules(self):
        extraflags = {
            module: [] for module in self.repo.qc_modules
        }

        flags_configdefs = ['-DRM_NO_AUTO_HEADER'] + [
            ('-D%s=%s' % (key, value)) if value else ('-D%s' % key)
                for key, value in self.qc_defs.items()
        ]

        flags_autocvars = ['-DRM_AUTOCVARS']

        for name, module in self.repo.qc_modules.items():
            if not module.needs_auto_header:
                extraflags[name] += flags_configdefs

        if self.autocvars == 'enable':
            for module in self.repo.qc_modules:
                extraflags[module] += flags_autocvars
        elif self.autocvars == 'compatible':
            extraflags['server'] += flags_autocvars

            self.configure_qc_module(
                'client',
                qcc_cmd=self.qcc_cmd,
                qcc_flags=self.qcc_flags + flags_autocvars + extraflags['client'],
                dat_expected_name='csprogs',
                dat_final_name='rocketminsta_cl_autocvars',
                cvar='csqc_progname_alt',
            )
        elif self.autocvars != 'disable':
            raise ValueError(
                "'autocvars' must be one of: 'enable', 'disable', 'compatible'; got %r instead" % self.autocvars
            )

        self.configure_qc_module(
            'server',
            qcc_cmd=self.qcc_cmd,
            qcc_flags=self.qcc_flags + extraflags['server'],
            dat_expected_name='progs',
            dat_final_name='rocketminsta_sv',
            cvar='sv_progs',
        )

        self.configure_qc_module(
            'client',
            qcc_cmd=self.qcc_cmd,
            qcc_flags=self.qcc_flags + extraflags['client'],
            dat_expected_name='csprogs',
            dat_final_name='rocketminsta_cl',
            cvar='csqc_progname',
        )

        self.configure_qc_module(
            'menu',
            qcc_cmd=self.qcc_cmd,
            qcc_flags=self.qcc_flags + extraflags['menu'],
            dat_expected_name='menu',
            dat_final_name='menu',
        )

    def should_install_qc_module(self, name):
        return name != 'menu'

    def should_build_package(self, pkg):
        return (not (
            pkg.name.startswith('c_') or
            pkg.name.startswith('o_')
        )) or pkg.name in self.extra_packages

    def call_hook(self, hook, **kwargs):
        if hook not in self.hooks:
            return

        log.debug('Calling hook %r (keywords=%r)', hook, kwargs)
        return self.hooks[hook](
            build_info=self,
            log=util.logger(__name__, 'hook', hook),
            **kwargs
        )

    def get_qc_defs(self):
        defs = {
            'RM_BUILD_DATE': '"%s (%s)"' % (self.date_string, self.comment),
            'RM_BUILD_NAME': '"%s"' % (self.name),
            'RM_BUILD_VERSION': '"%s"' % self.version,
            'RM_BUILD_MENUSUM': '"%s"' % self.repo.qchash_menu.hexdigest(),
            'RM_BUILD_SUFFIX': '"%s"' % self.suffix,
        }

        for name, pkg in self.repo.packages.items():
            if self.should_build_package(pkg):
                defs['RM_SUPPORT_PKG_%s' % name] = None

        return defs

    def abort_if_failed(self):
        if self.failed:
            raise errors.BuildStepAborted

    def add_async_task(self, name, task):
        log.debug("Added task for %s", name)

        def wrapped_task():
            result = task()
            log.debug("Finished task for %s", name)
            return result

        subs = name.split('.')
        lists = [self.futures, self.tasks.setdefault(name, [])] + [
            self.tasks.setdefault('.'.join(subs[:i]), []) for i in range(1, len(subs))
        ]

        future = self.executor.submit(wrapped_task)

        for lst in lists:
            lst.append(future)

    def finish_async_tasks(self):
        done, not_done = futures.wait(self.futures, return_when=futures.FIRST_EXCEPTION)

        if not_done:
            self.failed = True
            for future in not_done:
                future.cancel()

        for future in done:
            future.result()

        self.executor.shutdown()

    def wait_for_tasks(self, *tasknames):
        for taskname in tasknames:
            log.debug("Waiting for %s", taskname)
            for future in self.tasks[taskname]:
                future.result()
            log.debug("Done waiting for %s", taskname)


class Repo(object):
    MAX_VERSION = 1

    def __init__(self, path):
        self.version = 0
        self.packages = {}
        self.qc_modules = {}
        self.root = path
        self.qchash_menu = None

    @property
    def root(self):
        return self._root

    @root.setter
    def root(self, path):
        self.init_paths(path)

    @property
    def qcsrc(self):
        return self._qcsrc

    @property
    def modfiles(self):
        return self._modfiles

    def init_paths(self, path):
        self._root = util.directory(path).resolve()

        try:
            with (self._root / '.rmbuild_repoversion').open() as f:
                self.version = int(f.read().strip())
        except FileNotFoundError:
            self.version = 0

        if self.version > self.MAX_VERSION:
            raise errors.VersionError('Repo version is %i, maxiumum supported is %i. Please update rmbuild.' %
                                      (self.version, self.MAX_VERSION))

        self._qcsrc = util.directory(self._root / 'qcsrc')
        self._modfiles = util.directory(self._root / 'modfiles')

        with util.in_dir(self.root):
            self.rm_branch = util.git('rev-parse', '--abbrev-ref', 'HEAD')
            self.rm_version = util.git('describe', '--tags', '--dirty')

        self.init_packages()
        self.init_qc_modules()

    def init_packages(self):
        for pdir in self.root.glob('*.pk3dir'):
            self.packages[pdir.stem] = package.construct(pdir.stem, pdir)

    def init_qc_modules(self):
        for name in ('server', 'client', 'menu'):
            self.qc_modules[name] = qcmodule.QCModule(name, self.qcsrc / name)

    def build(self, *buildinfo_args, **buildinfo_kwargs):
        self.update_qcsrc_hashes()
        build_info = BuildInfo(self, *buildinfo_args, **buildinfo_kwargs)
        log.info("Build started: %s %s (%s)", build_info.name, self.rm_version, build_info.comment)

        util.clear_directory(build_info.output_dir)

        auto_header_needed = False
        for qc in self.qc_modules.values():
            if qc.needs_auto_header:
                auto_header_needed = True
                break

        with util.in_dir(build_info.temp_dir):
            if auto_header_needed:
                self.generate_qc_header(build_info)

            self.build_qc_modules(build_info)
            self.build_packages(build_info)
            self.install_qc_modules(build_info)
            self.copy_static_files(build_info)
            self.update_rm_cfg(build_info)
            self.create_server_package(build_info)
            build_info.finish_async_tasks()

        delta = datetime.datetime.now() - build_info.date

        log.info(
            "Build finished: %s %s (%s), target: %r, build time: %s",
            build_info.name,
            self.rm_version,
            build_info.comment,
            str(build_info.output_dir),
            delta
        )

        build_info.call_hook('post_build')
        return build_info

    def update_qcsrc_hashes(self):
        log.info("Hashing the QC source files")
        self.qchash_menu = self.qc_modules['menu'].compute_hash(util.hash_constructor())

    def generate_qc_header(self, build_info):
        log.info("Generating the rm_auto header")

        with open(str(self.qcsrc / 'common' / 'rm_auto.qh'), 'w') as header:
            for key, value in build_info.qc_defs.items():
                if value:
                    header.write('#define %s %s\n' % (key, value))
                else:
                    header.write('#define %s\n' % key)

    def build_packages(self, build_info):
        for name, pkg in self.packages.items():
            if not build_info.should_build_package(pkg):
                continue

            def task(name=name, pkg=pkg, build_info=build_info):
                log.debug('build() for %s', name)
                pkg.build(build_info)
                build_info.built_packages.append(pkg)

            build_info.add_async_task("pkg.%s" % name, task)

    def build_qc_modules(self, build_info):
        built = build_info.built_qc_modules

        for name, module in self.qc_modules.items():
            built[name] = []
            for config in build_info.qc_module_config[name]:
                def task(name=name, built=built, module=module, build_info=build_info, config=config):
                    built[name].append(module.build(build_info, config))
                build_info.add_async_task("qc.%s" % name, task)

    def install_qc_module(self, build_info, built_module):
        for fpath in filter(lambda p: p.suffix in util.QC_INSTALL_FILEEXT, built_module.iterdir()):
            util.copy(fpath, build_info.output_dir)

    def install_qc_modules(self, build_info):
        def task():
            build_info.wait_for_tasks('qc')
            log.info("Installing QC modules")

            for name, dirs in build_info.built_qc_modules.items():
                if not build_info.should_install_qc_module(name):
                    continue

                for module in dirs:
                    self.install_qc_module(build_info, module)
        build_info.add_async_task('copyqc', task)

    def copy_static_files(self, build_info):
        def task():
            log.info("Copying static files")
            util.copy_tree(self.modfiles, build_info.output_dir)
        build_info.add_async_task('static', task)

    def update_rm_cfg(self, build_info):
        def task():
            build_info.wait_for_tasks('static', 'pkg')

            log.info("Updating rocketminsta.cfg")

            with (build_info.output_dir / 'rocketminsta.cfg').open('a') as rmcfg:
                rmcfg.write('\n\n// The rest of this file was autogenerated by rmbuild\n\n')
                rmcfg.write('rm_clearpkgs\n')

                for pkg in build_info.built_packages:
                    rmcfg.write('rm_putpackage %s\n' % pkg.metafile_name)

                rmcfg.write('\n')

                for name, cfgs in build_info.qc_module_config.items():
                    for cfg in cfgs:
                        if cfg.cvar:
                            rmcfg.write('set %s %s.dat\n' % (cfg.cvar, cfg.dat_final_name))

                rmcfg.write('\n')
        build_info.add_async_task('rmcfg', task)

    def create_server_package(self, build_info):
        if build_info.server_package == 'none':
            return

        if build_info.server_package not in ('pk3', 'pk3dir'):
            raise ValueError(build_info.server_package)

        def task():
            build_info.wait_for_tasks('static', 'qc', 'copyqc', 'rmcfg')
            log.info("Creating the server-side package")

            files = []
            dirs = []

            def add_files(path):
                for p in path.iterdir():
                    if p.suffix in ('.pk3', '.pk3dir'):
                        continue

                    if p.is_symlink():
                        raise errors.PathError(p, "symbolic links are not supported here")

                    if p.is_dir():
                        dirs.append(p.relative_to(build_info.output_dir))
                        add_files(p)
                    else:
                        files.append(p.relative_to(build_info.output_dir))

            add_files(build_info.output_dir)

            pk3dir = util.make_directory(
                build_info.output_dir / ('zzz-rm-server-%s.pk3dir' % build_info.version)
            )

            for d in dirs:
                util.make_directory(pk3dir / d)

            for f in files:
                (build_info.output_dir / f).replace(pk3dir / f)

            for d in sorted(dirs, reverse=True):
                (build_info.output_dir / d).rmdir()

            if build_info.server_package == 'pk3':
                shutil.make_archive(str(pk3dir.with_suffix('')), 'zip', str(pk3dir),
                                    logger=util.logger(__name__, 'srvpkg'))
                pk3dir.with_suffix('.zip').rename(pk3dir.with_suffix('.pk3'))
                shutil.rmtree(str(pk3dir))

        build_info.add_async_task('srvpkg', task)

    def __repr__(self):
        return 'Repo(%r)' % str(self._root)
