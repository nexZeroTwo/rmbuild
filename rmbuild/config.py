
import inspect

from . import build
from . import util

log = util.logger(__name__)

build_args = {}
install_options = {}


def apply(fpath, repo):
    cfg = {
        'util': util,
        'repo': repo
    }

    fpath = str(fpath)
    log.info('Using configuration file %r', fpath)

    with open(fpath) as f:
        code = compile(f.read(), fpath, 'exec')
        exec(code, cfg, cfg)

    for param in tuple(inspect.signature(build.BuildInfo).parameters.keys())[2:]:
        if param in cfg:
            build_args[param] = cfg[param]

    install_options.update({
        'dirs': cfg.get('install_dirs', []),
        'linkdirs': cfg.get('install_linkdirs', [])
    })
