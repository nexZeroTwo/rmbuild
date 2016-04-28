
import logging

from . import config
from . import build
from . import install


def main(argv):
    logging.basicConfig(level=logging.INFO)

    try:
        cfgname = argv[1]
    except IndexError:
        cfgname = 'config.py'

    config.apply(cfgname)
    binfo = build.Repo(config.repo_path).build(**config.build_args)

    for path in config.install_options['dirs']:
        install.install(binfo, path, link=False)

    for path in config.install_options['linkdirs']:
        install.install(binfo, path, link=True)
