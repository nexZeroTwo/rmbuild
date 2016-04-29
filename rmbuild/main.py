
import logging
import argparse
import pathlib

from . import config
from . import build
from . import install
from . import util
from . import errors

log = util.logger(__name__)


def parse_args(argv):
    p = argparse.ArgumentParser(
        prog=argv[0],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
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
        default='.',
        type=type_dir,
        help="path to the RocketMinsta git repository (working tree)"
    )

    p.add_argument(
        '-g', '--git',
        default='git',
        help="the git executable to use"
    )

    p.add_argument(
        '-v', '--verbose',
        action='store_const',
        const=logging.DEBUG,
        default=logging.INFO,
        help='be noisy',
        dest='log_level'
    )

    p.add_argument(
        'config',
        nargs='?',
        default='config.py',
        type=type_file,
        help="path to the build configuration file"
    )

    return p.parse_args(args=argv[1:])


def main(argv):
    if pathlib.Path(argv[0]).name == '__main__.py':
        argv[0] = 'rmbuild'

    args = parse_args(argv)
    logging.basicConfig(level=args.log_level)
    util.GIT_EXECUTABLE = args.git

    log.info('Using RocketMinsta repository %r', str(args.path))

    repo = build.Repo(args.path)
    config.apply(args.config, repo)
    binfo = repo.build(**config.build_args)

    for path in config.install_options['dirs']:
        install.install(binfo, path, link=False)

    for path in config.install_options['linkdirs']:
        install.install(binfo, path, link=True)
