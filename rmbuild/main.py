
import logging
import argparse
import pathlib

from .compat import *

from . import config
from . import build
from . import util
from . import errors

log = util.logger(__name__)


def parse_args(argv, defaults_overrides=None):
    defaults = {
        'path': '.',
        'git': 'git',
        'config': 'config.py',
    }

    if defaults_overrides is not None:
        defaults.update(defaults_overrides)

    p = argparse.ArgumentParser(
        prog=argv[0],
        fromfile_prefix_chars='@',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=False
    )

    def type_dir(val):
        try:
            return util.directory(val).resolve()
        except errors.PathError as e:
            raise argparse.ArgumentTypeError(e)

    def type_file(val):
        try:
            return util.file(val).resolve()
        except errors.PathError as e:
            raise argparse.ArgumentTypeError(e)

    p.add_argument(
        '-p', '--path',
        default=defaults['path'],
        type=type_dir,
        help="Path to the RocketMinsta git repository (working tree)."
    )

    p.add_argument(
        '-g', '--git',
        default=defaults['git'],
        help="The git executable to use."
    )

    p.add_argument(
        '-r', '--rebuild',
        action='store_true',
        help="Rebuild all packages and QC modules even if cached versions exist.\n"
             "If caching is in use, the cached versions will be updated."
    )

    p.add_argument(
        'config',
        nargs='?',
        default=defaults['config'],
        type=type_file,
        help="Path to the build configuration file."
    )

    p.add_argument(
        '-a', '--args',
        nargs=argparse.REMAINDER,
        help="All remaining arguments are passed to the config in 'argv'",
        dest='config_argv',
        default=[]
    )

    p.add_argument(
        '-v', '--verbose',
        action='store_const',
        const=logging.DEBUG,
        default=logging.INFO,
        help="Be noisy.",
        dest='log_level'
    )

    p.add_argument(
        '-h', '--help',
        action='help',
        help="Print this help message and exit."
    )

    return p.parse_args(args=argv[1:])


def main(argv, defaults_overrides=None):
    if pathlib.Path(argv[0]).name == '__main__.py':
        argv[0] = 'rmbuild'

    args = parse_args(argv, defaults_overrides)
    logging.basicConfig(level=args.log_level)
    util.GIT_EXECUTABLE = args.git

    log.info('Using RocketMinsta repository %r', str(args.path))

    with util.in_dir(args.path.resolve()):
        repo = build.Repo(args.path)
        build_args, install_options = config.apply(args.config, repo, args.config_argv)

        if args.rebuild:
            build_args['force_rebuild'] = True

        binfo = repo.build(**build_args)

        for path in install_options['dirs']:
            binfo.install(path, link=False)

        for path in install_options['linkdirs']:
            binfo.install(path, link=True)

        binfo.call_hook('post_install')
