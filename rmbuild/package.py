
import zipfile
import pathlib
import itertools
import re

from .compat import *
from .errors import *

from . import util


class Package(object):
    OUTPUT_NAME_FORMAT = "zzz-rm-%(name)s-%(hash)s.pk3"
    SRC_IMAGE_SUFFIXLIST = ['.tga', '.png']

    def __init__(self, name, path):
        self.name = name
        self.path = util.directory(path)
        self._hash = None
        self.log = util.logger(__name__, name)

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.name, str(self.path))

    def invalidate_hash(self):
        self._hash = None

    @property
    def hash(self):
        if self._hash is not None:
            return self._hash
        self._hash = util.hash_path(self.path, namefilter=self.filter_filename)
        self._hash.update(util.HASH_PKG_APPEND_BYTES)
        return self._hash

    @property
    def output_file_name(self):
        return self.OUTPUT_NAME_FORMAT % {
            'name': self.name,
            'hash': self.hash.hexdigest(),
        }

    @property
    def metafile_name(self):
        return '_rmbuild_metafile_%s_%s.txt' % (self.name, self.hash.hexdigest())

    def filter_filename(self, filename):
        return filename not in (
            "compressdirs",
            "_md5sums",
        ) and not re.match(r'^_pkginfo_.*\.txt$', filename)

    def files(self):
        for fpath in self.path.glob('**/*'):
            rpath = fpath.relative_to(self.path).as_posix()
            if self.filter_filename(rpath):
                yield fpath, rpath

    def _create_pk3(self, build_info):
        self.log.info("Making package %s", self.output_file_name)

        output_path = build_info.output_dir / self.output_file_name
        pk3 = zipfile.ZipFile(str(output_path), 'w', zipfile.ZIP_DEFLATED)
        return pk3

    def _add_metafile(self, build_info, pk3):
        self.log.debug("Adding metafile: %s", self.metafile_name)

        pkginfo = (
            "%s %s client-side package %s (%s)\n"
            "Built at %s\n"
        ) % (
            build_info.name,
            build_info.version,
            self.name,
            build_info.comment,
            build_info.date_string,
        )

        info = zipfile.ZipInfo(str(self.path))
        info.filename = self.metafile_name
        info.external_attr = 0o644 << 16    # -r-wr--r-- permissions
        pk3.writestr(info, pkginfo)

    def _read_compressdirs(self):
        compress_tga = []

        try:
            cdirs = map(lambda p: self.path / p, (self.path / 'compressdirs').read_text().strip().split('\n'))
        except FileNotFoundError:
            return compress_tga

        for cdir in cdirs:
            for fpath in cdir.iterdir():
                if fpath.is_file() and fpath.suffix in self.SRC_IMAGE_SUFFIXLIST:
                    compress_tga.append(fpath)

        return compress_tga

    def _may_compress_image(self, fpath):
        blacklist = [
            'gfx/iceland.tga',
            'gfx/madoka-rune.tga',
        ]

        fpath = pathlib.PurePosixPath(fpath.relative_to(self.path).as_posix())

        for pattern in blacklist:
            if fpath.match(pattern):
                return False

        return True

    def _compress_tga(self, build_info):
        cmap = {}
        extrafiles = []

        if not build_info.compress_gfx:
            return cmap, extrafiles

        if build_info.compress_gfx_all:
            tgalist = [fpath for fpath, rpath in self.files() if fpath.suffix.lower() in self.SRC_IMAGE_SUFFIXLIST]
        else:
            tgalist = self._read_compressdirs()

        if not tgalist:
            return cmap, extrafiles

        from PIL import Image

        tdir = util.make_directory(build_info.temp_dir / ('pkg_compresstga_' + self.name))

        for tga in tgalist:
            if not self._may_compress_image(tga):
                continue

            build_info.abort_if_failed()

            rel = tga.relative_to(self.path).with_suffix('.jpg')
            abs = (tdir / rel)
            cmap[tga] = (abs, rel.as_posix())
            util.make_directory(cmap[tga][0].parent)

            if tga.is_symlink():
                abs.symlink_to(tga.resolve().relative_to(tga.parent).with_suffix('.jpg'))
                continue

            with abs.open('wb') as jpeg:
                self.log.debug('Converting %r to JPEG', str(tga))

                img = Image.open(str(tga))
                img.save(jpeg, format='JPEG', quality=build_info.compress_gfx_quality, optimize=True)

                if img.mode == 'RGBA':
                    *rgb, alpha = img.split()
                    colors = alpha.getcolors(1)

                    if not colors or colors[0][1] < 255:
                        alphajpeg = abs.with_name(tga.stem + "_alpha").with_suffix(abs.suffix)
                        alphajpeg_rel = rel.with_name(tga.stem + "_alpha").with_suffix(abs.suffix)
                        extrafiles.append((alphajpeg, alphajpeg_rel.as_posix()))

                        self.log.debug('Image %r has a non-white alpha channel, saving it to %r', str(tga), str(alphajpeg))
                        alpha.save(str(alphajpeg), format='JPEG', quality=build_info.compress_gfx_quality, optimize=True)


        return cmap, extrafiles

    def _build(self, build_info):
        use_cache = bool(build_info.cache_dir and build_info.cache_pkg)

        if use_cache:
            cache_dir = util.make_directory(build_info.cache_dir / 'pkg')
            cached_pkg = cache_dir / self.output_file_name

            if cached_pkg.exists() and not build_info.force_rebuild:
                self.log.info('Using a cached version (%r)', str(cached_pkg))
                util.copy(cached_pkg, build_info.output_dir)
                return

        cmap, extrafiles = self._compress_tga(build_info)
        pk3 = self._create_pk3(build_info)

        for fpath, rpath in itertools.chain(self.files(), extrafiles):
            build_info.abort_if_failed()

            if fpath in cmap:
                self.log.debug("Adding empty placeholders for %r", rpath)

                for suffix in self.SRC_IMAGE_SUFFIXLIST:
                    info = zipfile.ZipInfo(str(self.path))
                    info.filename = str(pathlib.PurePath(rpath).with_suffix(suffix))
                    info.external_attr = 0o644 << 16    # -r-wr--r-- permissions
                    pk3.writestr(info, "")

                fpath, rpath = cmap[fpath]

            if fpath.is_symlink():
                linkpath = fpath.resolve().relative_to(fpath.parent).as_posix()
                self.log.debug("Adding link: %s -> %s", rpath, linkpath)
                info = zipfile.ZipInfo(str(self.path))
                info.filename = rpath

                # Make it a symlink
                info.external_attr |= 0o0120000 << 16

                # Another bit of undocumented magic to make symlinks work on windows
                # The zipfile module sucks
                info.create_system = 3

                pk3.writestr(info, linkpath)
            else:
                self.log.debug("Adding file: %s [%s]", rpath, str(fpath))
                pk3.write(str(fpath), rpath)

        self._add_metafile(build_info, pk3)
        pk3.close()
        self.log.info("Done")

        build_info.abort_if_failed()
        build_info.call_hook('post_build_pk3',
            package=self,
            pk3_path=build_info.output_dir / self.output_file_name
        )

        if use_cache:
            self.log.info('Caching for reuse (%r)', str(cached_pkg))
            util.copy(build_info.output_dir / self.output_file_name, cached_pkg)

    def build(self, build_info):
        if build_info.link_pk3dirs:
            (build_info.output_dir / self.output_file_name).with_suffix('.pk3dir').symlink_to(self.path.resolve())
        else:
            self._build(build_info)


class LateBuildingPackage(Package):
    @property
    def hash(self):
        if self._hash is None:
            raise PackageError(self, "Tried to read hash too early")
        return self._hash


class QCPackage(LateBuildingPackage):
    def files(self):
        for path in self._qc_modules:
            for fpath in filter(lambda p: p.suffix in util.QC_INSTALL_FILEEXT, path.iterdir()):
                yield (fpath, fpath.name)


class CSQCPackage(QCPackage):
    def _compute_hash(self):
        h = util.hash_constructor()

        for path in self._qc_modules:
            util.hash_path(path, root=path.parent, hashobject=h)

        return h

    def build(self, build_info):
        build_info.wait_for_tasks('qc.client')
        self._qc_modules = build_info.built_qc_modules['client']
        self._hash = self._compute_hash()
        self._build(build_info)


class MenuPackage(QCPackage):
    def build(self, build_info):
        build_info.wait_for_tasks('qc.menu')
        self._qc_modules = build_info.built_qc_modules['menu']
        self._hash = build_info.repo.qchash_menu.copy()
        self._build(build_info)


def construct(*args, **kwargs):
    return {
        'csqc': CSQCPackage,
        'menu': MenuPackage,
    }.get(args[0], Package)(*args, **kwargs)
