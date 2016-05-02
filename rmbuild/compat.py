
import inspect
import pathlib

FileNotFoundError = getattr(__builtins__, 'FileNotFoundError', IOError)


try:
    inspect.signature
except AttributeError:
    def get_parameter_names(func):
        try:
            return tuple(inspect.getargspec(func).args)
        except TypeError:
            # maybe we're trying to examine a class constructor?
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
