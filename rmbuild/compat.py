
import inspect
import pathlib
import sys

FileNotFoundError = getattr(__builtins__, 'FileNotFoundError', IOError)


try:
    inspect.signature
except AttributeError:
    def get_parameter_names(func):
        try:
            return tuple(inspect.getargspec(func).args)
        except TypeError:
            # maybe we're trying to examine a class initializer?
            return get_parameter_names(func.__init__)[1:]
else:
    def get_parameter_names(func):
        return tuple(inspect.signature(func).parameters.keys())


try:
    pathlib.Path.read_text
except AttributeError:
    def __compat_pathlib_Path_read_text(self, encoding=None, errors=None):
        with self.open(encoding=encoding, errors=errors) as f:
            return f.read()

    pathlib.Path.read_text = __compat_pathlib_Path_read_text


if sys.version_info < (3, 3):
    def __compat_pathlib_Path_replace(self, target):
        target = pathlib.Path(target)

        if target.exists():
            target.unlink()

        self.rename(target)

    pathlib.Path.replace = __compat_pathlib_Path_replace


try:
    pathlib.Path("/honoka/kotori.umi").with_suffix('')
except ValueError:
    __orig_with_suffix = pathlib.Path.with_suffix

    def __compat_pathlib_Path_with_suffix(self, suffix):
        if not suffix:
            return self.__class__(str(__orig_with_suffix(self, '.wtf'))[:-4])
        return __orig_with_suffix(self, suffix)

    pathlib.Path.with_suffix = __compat_pathlib_Path_with_suffix
