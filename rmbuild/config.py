
import inspect

from . import build
from . import util

build_args = {}
install_options = {}
repo_path = '.'


def apply(fpath):
    def get_repo(path):
        return build.Repo(path)

    cfg = {
        'util': util,
        'get_repo': get_repo,
    }

    with open(str(fpath)) as f:
        code = compile(f.read(), fpath, 'exec')
        exec(code, cfg, cfg)

    if 'repo_path' in cfg:
        global repo_path
        repo_path = cfg['repo_path']

    for param in tuple(inspect.signature(build.BuildInfo).parameters.keys())[2:]:
        if param in cfg:
            build_args[param] = cfg[param]

    if 'git_cmd' in cfg:
        util.GIT_EXECUTABLE = cfg.git_cmd

    install_options.update({
        'dirs': cfg.get('install_dirs', []),
        'linkdirs': cfg.get('install_linkdirs', [])
    })
