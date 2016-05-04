
################################################################################
#                                                                              #
#   Example configuration file for rmbuild.                                    #
#                                                                              #
#   Copy this file into your clone of the RocketMinsta git repository and      #
#   customize it for your needs.                                               #
#                                                                              #
#   None of the options are required and any may be omitted (defaults will     #
#   then be used), but you'll most likely want to provide at least one         #
#   installation directory. Many of the options in this file are commented     #
#   out, remove the '#' symbol in front of those if you want to change them.   #
#                                                                              #
#   Any Python 3 code is valid here. See the Advanced section for more info.   #
#                                                                              #
#   Paths are relative to the RM repository working tree, unless absolute.     #
#                                                                              #
#   For Windows, prefix path strings with r, or use forward slashes.           #
#   Examples:                                                                  #
#       r'C:\this\is\valid'                                                    #
#       'D:/this/is/also/valid'                                                #
#       'F:\this\is\not\valid'                                                 #
#                                                                              #
################################################################################


################################################################################
#                                                                              #
#   Basic section.                                                             #
#                                                                              #
#   Options you likely want to customize.                                      #
#                                                                              #
################################################################################

#
#   qcc_cmd
#
#   System command used to run the QuakeC compiler.
#   Can be a full path to the executable, or relative to $PATH.
#
#   Do not put commandline arguments here, refer to the Advanced section below
#   if you need to pass any.
#
#   The value below is the default.
#

#qcc_cmd = 'rmqcc'


#
#   install_dirs
#
#   List of directories to copy the mod files into.
#   All of them must already exist and be writable.
#   Files retained from a previous installation will be removed first.
#   Any other files will be left untouched.
#
#   The default value is an empty list (no installation).
#
#   Example: install RM to the current user's ~/.nexuiz/data directory.
#   util.expand is used to expand ~ to the full home path.
#

install_dirs = [util.expand('~/.nexuiz/data/')]

#
#   Example with multiple directories:
#

#install_dirs = ['/some/path', '/some/other/path', util.expand('~/rm')]


#
#   extra_packages
#
#   By default, all pk3dirs present in the RM repo directory will be built
#   into client-side packages (pk3s), except those prefixed with o_ or c_.
#
#   Here you can specify a list of additional o_ and c_ packages include.
#
#   o_ stands for "optional", those are part of RM and are tracked by git.
#   c_ stands for "custom", those are user-supplied and ignored by git.
#
#   Prefix your own packages with c_.
#
#   The value below is the default.
#

#extra_packages = []

#
#   Example: include the optional Ayumi package and some custom skins:
#

#extra_packages = ['o_ayumi', 'c_mycoolskins']


#
#   threads
#
#   Parallelize some parts of the build process, using up to this many threads.
#   Can speed up builds, but may make error messages harder to read in case
#   anything goes wrong.
#
#   Use 1 for fully sequential builds.
#
#   The value below is the default.
#

#threads = 8


#
#   comment
#
#   An arbitrary human-readable string identifying your RM build.
#
#   The value below is the default.
#

# comment = "custom build"


################################################################################
#                                                                              #
#   Advanced section.                                                          #
#                                                                              #
#   Fine-tuning, development options, etc.                                     #
#   Some Python knowledge is assumed.                                          #
#                                                                              #
#   ########################################################################   #
#                                                                              #
#   In addition to the standard Python builtins, the following names are       #
#   available in the global namespace:                                         #
#                                                                              #
#       * util: the rmbuild.util module                                        #
#       * repo: an rmbuild.build.Repo instance associated with the RM repo     #
#       * argv: list of arguments passed to rmbuild after -a/--args            #
#                                                                              #
################################################################################


#
#   output_dir
#
#   Intermediate build directory.
#   All mod files will be put here before installation.
#   It will be created if it doesn't already exist.
#
#   By default, an OS-specific temporary directory is used,
#   and removed after the build is finished.
#
#   * WARNING *
#   * THE CONTENTS OF THIS DIRECTORY WILL BE WIPED BEFORE BUILDING *
#
#   Example: separate persistent build directory per-branch,
#   inside /path/to/rm/repository/build/BRANCH_NAME.
#

#output_dir = util.path('build', repo.rm_branch)


#
#   install_linkdirs
#
#   Exactly like install_dirs, except files are symlinked to output_dir
#   instead of being copied.
#
#   You must, of course, specify an output_dir to use this,
#   otherwise dangling symlinks will be created.
#
#   Do not use this on Windows.
#
#   The value below is the default.
#

#install_linkdirs = []


#
#   qcc_flags
#
#   Additional options to pass to the QuakeC compiler.
#   Can be a list or a string.
#   If it's a string, it will be parsed with shlex in POSIX mode.
#   (https://docs.python.org/3/library/shlex.html#parsing-rules)
#
#   The default value is None (same as an empty string or list).
#
#   Example: enable optimizations (slower build, better performance):
#

qcc_flags = '-O2'

#
#   Example: no extra optimizations, treat warnings as errors
#   (recommended for developers):
#

#qcc_flags = '-Werror'


#
#   autocvars
#
#   Build QC modules with support for autocvars, and possibly other
#   DPRM-specific optimizations.
#
#   Such modules will not work on non-DPRM engines.
#
#   Possible values are:
#
#       * 'enable': enabled for all modules.
#       * 'disable': disabled for all modules.
#       * 'compatible': enabled for server, disabled for menu,
#          2 versions of CSQC are built: clients that claim to
#          support the required extensions get the optimized one,
#          others get a fallback that should run on most engines.
#
#   The value below is the default.
#

#autocvars = 'compatible'


#
#   cache_dir
#
#   Directory to store built QC modules and/or pk3s in, for later reuse.
#
#   Intended for developers to speed up test builds.
#
#   The default value is None (no caching).
#
#   Example: use the 'cache' directory inside the RM repo
#   (this path is ignored by git):
#

cache_dir = 'cache'


#
#   link_pk3dirs
#
#   Skip building of client-side pk3s altogether (except for 'special' ones).
#   Instead, create symlinks to the pk3dirs in the RM repo instead.
#
#   Intended for developers to speed up test builds.
#   Suitable for local servers only.
#
#   Do not use this on Windows.
#
#   The value below is the default.
#

#link_pk3dirs = False


#
#   compress_gfx
#
#   Convert most of the TGA textures to JPEG.
#   Slows builds down, but reduces pk3 sizes drastically.
#   Not recommened to disable for that reason.
#
#   Requires PIL (or a compatible fork, like Pillow).
#
#   The value below is the default.
#

#compress_gfx = True


#
#   compress_gfx_quality
#
#   Quality of the TGA->JPEG conversion, in the 0-100 range.
#   Higher means better quality, but less compression (larger file size).
#
#   The value below is the default.
#

#compress_gfx_quality = 85


#
#   suffix
#
#   Override the branch name.
#
#   The value below is the default.
#

#suffix = None


################################################################################
#                                                                              #
#   Hooks.                                                                     #
#                                                                              #
#   Hooks are callback functions invoked by the build system.                  #
#   They can be used to customize the distribution, install RM pk3s on your    #
#   web server, automatically update/restart your servers after a successful   #
#   build and installation, etc.                                               #
#                                                                              #
#   Hooks are ordinary Python 3 functions.                                     #
#                                                                              #
#   All arguments are passed as keywords.                                      #
#   This means that parameter names matter, but the order does not.            #
#   The following arguments are passed to all hooks:                           #
#                                                                              #
#       * build_info: an rmbuild.build.BuildInfo instance representing the     #
#         current build.                                                       #
#       * log: a logging.Logger instance.                                      #
#                                                                              #
#   For maximum compatibility, it's recommended to omit arguments you don't    #
#   use, and end the parameter list with a catch-all such as **rest.           #
#                                                                              #
################################################################################


#
#   hook_post_build
#
#   Called after the build is finished.
#
#   You can customize the distribution in build_info.output_dir,
#   the changes will be reflected in all installation directories.
#
#   No additional arguments.
#

"""
def hook_post_build(build_info, log, **rest):
    log.info("Yay! Finished building at %r", str(build_info.output_dir))
"""


#
#   hook_post_install
#
#   Called after the installation is finished for all directories.
#
#   No additional arguments.
#
#   Example: install all pk3s to the web server.
#   Just like with a normal install, previously installed RM pk3s will be
#   removed, and all other files will be left intact.
#

"""
def hook_post_install(build_info, log, **rest):
    build_info.install('/var/www/nexuiz-pk3s', pathfilter='*.pk3', link=False)
"""


#
#   hook_post_build_pk3
#
#   Called after a pk3 has been built, before it has been cached for reuse.
#
#   Additional arguments:
#       * pk3_path: full path to the pk3 (a pathlib.Path object)
#
#   Example: run the Leanify tool on each pk3 to reduce its size (very slow)
#   https://github.com/JayXon/Leanify
#

"""
def hook_post_build_pk3(log, pk3_path, **rest):
    util.logged_subprocess(['leanify', '-v', str(pk3_path)], logger=log)
"""











































































































































# P.S.: Honoka is best girl and HonoUmi is OTP.