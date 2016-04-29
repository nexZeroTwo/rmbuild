
import inspect

from . import build
from . import util

log = util.logger(__name__)


def apply(fpath, repo, argv):
    cfg = {
        'util': util,
        'repo': repo,
        'argv': argv,
    }

    build_args = {}

    fpath = str(fpath)
    log.info('Loading configuration file %r', fpath)

    with open(fpath) as f:
        code = compile(f.read(), fpath, 'exec')
        exec(code, cfg, cfg)

    for param in tuple(inspect.signature(build.BuildInfo).parameters.keys())[1:]:
        if param in cfg:
            build_args[param] = cfg[param]

    try:
        hooks = build_args['hooks']
    except KeyError:
        hooks = {}
        build_args['hooks'] = hooks

    for hook in filter(lambda key: key.startswith('hook_') and callable(cfg[key]), cfg):
        hooks[hook[5:]] = cfg[hook]

    install_options = {
        'dirs': cfg.get('install_dirs', []),
        'linkdirs': cfg.get('install_linkdirs', [])
    }

    return build_args, install_options
