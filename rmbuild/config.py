
import inspect

from . import build
from . import util

log = util.logger(__name__)

build_args = {}
install_options = {}
hooks = {}


def apply(fpath, repo):
    cfg = {
        'util': util,
        'repo': repo,
    }

    fpath = str(fpath)
    log.info('Using configuration file %r', fpath)

    with open(fpath) as f:
        code = compile(f.read(), fpath, 'exec')
        exec(code, cfg, cfg)

    for hook in filter(lambda key: key.startswith('hook_') and callable(cfg[key]), cfg):
        hooks[hook[5:]] = cfg[hook]

    for param in tuple(inspect.signature(build.BuildInfo).parameters.keys())[2:]:
        if param in cfg:
            build_args[param] = cfg[param]

    install_options.update({
        'dirs': cfg.get('install_dirs', []),
        'linkdirs': cfg.get('install_linkdirs', [])
    })


def call_hook(hook, *args, **kwargs):
    if hook not in hooks:
        return

    log.debug('Calling hook %r (args=%r, kwargs=%r)', hook, args, kwargs)
    return hooks[hook](*args, log=util.logger(__name__, 'hook', hook), **kwargs)
