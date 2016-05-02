
from .compat import *


class RMBuildException(Exception):
    pass


class RMBuildError(RMBuildException):
    pass


class PathError(RMBuildError):
    def __init__(self, path, message="Unusable path"):
        self.path = path
        self.message = message
        super().__init__("%s: %r" % (message, str(path)))


class PackageError(RMBuildError):
    def __init__(self, pkg, message):
        self.package = pkg
        self.message = message
        super().__init__("%s: %r" % (pkg.name, message))


class VersionError(RMBuildError):
    pass
