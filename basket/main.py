import collections
import os
import sys
import tarfile
import urllib
import xmlrpclib
import zipfile


PYPI_ENDPOINT = 'http://pypi.python.org/pypi'


def get_package_name(line):
    """Return a package name from a line in the ``requirements.txt``
    file.
    """
    idx = line.find('<')
    if idx == -1:
        idx = line.find('>')
        if idx == -1:
            idx = line.find('=')
    if idx == -1:
        return line
    return line[:idx].strip()


def get_name_and_version(filename):
    """Guess name and version of a package given its ``filename``."""
    idx = filename.rfind('.tar.gz')
    if idx == -1:
        idx = filename.rfind('.zip')
        if idx == -1:
            idx = filename.rfind('.')
    name, version = filename[:idx].rsplit('-', 1)
    return {'name': name, 'version': version}


class Basket(object):

    # Defined here so we can customize it for our tests. When we have
    # tests...
    err = sys.stderr
    out = sys.stdout
    root = os.environ.get('BASKET_ROOT') or os.path.expanduser('~/.basket')

    @property
    def client(self):
        """A wrapper around the XML-RPC client to create it on-demand.
        """
        # The 'is None' part is required, otherwise Python tries to
        # call 'self._client.__nonzero__' and the ServerProxy class
        # supposes that we are looking for the '__nonzero__' RPC
        # method. Hilarity does not ensue.
        if getattr(self, '_client', None) is None:
            self._client = xmlrpclib.ServerProxy(PYPI_ENDPOINT)
        return self._client

    @property
    def downloaded_packages(self):
        """Return information about downloaded packages."""
        if getattr(self, '_downloaded_packages', None) is None:
            self._downloaded_packages = []
            for filename in os.listdir(self.root):
                info = get_name_and_version(filename)
                info['filename'] = filename
                self._downloaded_packages.append(info)
        return self._downloaded_packages

    def _find_package_name(self, query):
        """Return information about the package that matches the
        query (case does not matter).

        PyPI may return more than one version of a package (e.g. when
        there are multiple concurrent stable releases). In this case,
        we return the latest one.
        """
        query = query.lower()
        candidates = []
        for info in self.client.search({'name': query}):
            if info['name'].lower() == query:
                candidates.append(info)
        if not candidates:
            return None
        return sorted(candidates, key=lambda info: info['version'])[-1]

    def _find_package_url(self, package, version):
        """Return the URL of the requested ``version`` of the
        ``package``.
        """
        # This is very basic indeed but should work. For most
        # packages. For me. YMMV.
        for info in self.client.release_urls(package, version):
            if info['python_version'] == 'source':
                return info['url']
        return None

    def _open_req_in_tar_archive(self, path):
        """Open the ``requires.txt`` file from the given TAR-gzipped
        archive.
        """
        with tarfile.open(path, 'r:gz') as archive:
            for info in archive:
                if info.name.endswith(
                    os.path.join('.egg-info', 'requires.txt')):
                    return archive.extractfile(info).readlines()
        return ()

    def _open_req_in_zip_archive(self, path):
        """Open the ``requires.txt`` file from the given zipped
        archive.
        """
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if info.filename.endswith(
                    os.path.join('.egg-info', 'requires.txt')):
                    return archive.open(info).readlines()
        return ()

    def _find_requirements(self, path):
        """Look at the package at ``path`` and return a list of
        required packages.

        This is not bulletproof at all and has the following
        limitations:

        - it only records the package name and ignore specific
          requirements (e.g. "docutils>=0.7"). This may be a problem
          for packages that explictly require a version that is not
          the latest;

        - it records optional requirements (which may be a good
          thing, though).
        """
        requirements = []
        if tarfile.is_tarfile(path):
            lines = self._open_req_in_tar_archive(path)
        elif zipfile.is_zipfile(path):
            lines = self._open_req_in_zip_archive(path)
        else:
            self.print_err('Could not open "%s" (unknown archive '
                           'format).' % path)
            return ()
        for line in lines:
            line = line.strip()
            if line and not line.startswith('['):
                requirements.append(get_package_name(line))
        return requirements

    def _has_package(self, package, version):
        for info in self.downloaded_packages:
            if (info['name'], info['version']) == (package, version):
                return True
        return False

    def _download(self, package, version, url):
        self.downloaded_packages.append({'name': package, 'version': version})
        path = os.path.join(self.root, url[url.rfind('/') + 1:])
        urllib.urlretrieve(url, path)
        return path

    def print_msg(self, msg):
        """Print ``msg`` followed by a newline character on the
        standard output.
        """
        self.out.write(msg + os.linesep)

    def print_err(self, err):
        """Print ``err`` followed by a newline character on the
        standard error.
        """
        self.err.write(err + os.linesep)

    def cmd_init(self):
        """Initialize Basket directory."""
        if os.path.exists(self.root):
            self.print_err('A file or directory already exists '
                           'at "%s".' % self.root)
            return 1
        os.makedirs(self.root)
        self.print_msg('Repository has been created: %s' % self.root)
        return 0

    def cmd_list(self, packages=()):
        """List all downloaded packages (or only requested ones)."""
        show_all = len(packages) == 0
        requested = set([name.lower() for name in packages])
        left = set(requested)
        for info in self.downloaded_packages:
            matches = info['name'].lower() in requested
            if show_all or matches:
                self.print_msg('%(name)s %(version)s' % info)
                if not show_all:
                    try:
                        left.remove(info['name'].lower())
                    except KeyError:
                        # we have already seen another version of this package
                        pass
        for name in left:
            self.print_err('Package "%s" is not installed (or it is '
                           'there but you mistyped the package name).' % name)

    def cmd_download(self, packages):
        """Download requested packages (if we do not have the latest
        version already) as well as their requirements.
        """
        self.packages = collections.deque(packages)
        while self.packages:
            package = self.packages.pop()
            info = self._find_package_name(package)
            if info is None:
                self.print_err(
                    'Could not find any package named "%s".' % package)
                continue
            url = self._find_package_url(info['name'], info['version'])
            if url is None:
                self.print_err(
                    'Could not find a suitable distribution for '
                    '%(name)s %(version)s.' % info)
                continue
            if self._has_package(info['name'], info['version']):
                self.print_msg(
                    '%(name)s is already up to date (%(version)s).' % info)
                continue
            path = self._download(info['name'], info['version'], url)
            self.print_msg('Added %(name)s %(version)s.' % info)
            requirements = self._find_requirements(path)
            if requirements:
                self.print_msg('  -> requires: %s' % ', '.join(requirements))
                self.packages.extendleft(requirements)
        return 0

    def cmd_prune(self, packages=()):
        """Keep only the latest version of each downloaded package (or
        only those that are requested.
        """
        requested = set([name.lower() for name in packages])
        left = set(requested)
        downloaded = collections.defaultdict(lambda: [])
        for info in self.downloaded_packages:
            downloaded[info['name'].lower()].append(info)
        prune_all = len(requested) == 0
        for name in sorted(downloaded.keys()):
            if not prune_all and name not in requested:
                continue
            if len(downloaded[name]) == 1:
                self.print_msg('%s has only one version. Nothing '
                               'to prune.' % downloaded[name][0]['name'])
                if not prune_all:
                    left.remove(name)
                continue
            if not prune_all:
                left.remove(name)
            versions = downloaded[name]
            sorted(versions, key=lambda info: info['version'])
            latest = versions[-1]['version']
            for filename in [info['filename'] for info in versions[:-1]]:
                os.remove(os.path.join(self.root, filename))
                self.print_msg('Removed %s %s (kept %s).' % (
                        info['name'], info['version'], latest))
        for name in left:
            self.print_err('Package "%s" is not installed (or it is '
                           'there but you mistyped the package name).' % name)
        return 0

    def cmd_update(self, packages=()):
        """Check whether we have the latest version of the requested
        packages (or all downloaded ones if ``packages`` is not given)
        and download it it we do not.

        If a new version is downloaded, the old version is kept. This
        is a feature.
        """
        if not packages:
            packages = []
            for info in self.downloaded_packages:
                # record multiple-versions of packages only once
                if info['name'] not in packages:
                    packages.append(info['name'])
            # reverse the order to please 'cmd_download()'
            packages.sort(key=lambda name: name.lower(), reverse=True)
        return self.cmd_download(packages)

    def syntax_error(self, command=None, help=False):
        """Print help about the syntax of the command-line."""
        if not help:
            self.print_err('Wrong syntax.')
        if command in (None, 'init'):
            self.print_err('Initialize a new repository (%s):' % self.root)
            self.print_err('    basket init')
        if command in (None, 'download'):
            self.print_err('Download one or more packages:')
            self.print_err('    basket download <package1> <package2> ...')
        if command in (None, 'list'):
            self.print_err('List all downloaded packages (or only the '
                           'requested ones):')
            self.print_err('    basket list [<package1> <package2> ...]')
        if command in (None, 'prune [<package1> <package2> ...]'):
            self.print_err('Keep only the latest version of all packages (or '
                           'only the requested ones):')
            self.print_err('    basket prune')
        if command in (None, 'update'):
            self.print_err('Download latest version of all packages (or '
                           'only the requested ones) if we do not already '
                           'have them:')
            self.print_err('    basket update [<package1> <package2> ...]')
        if command is None:
            self.print_err('Install from a Basket directory:')
            self.print_err('    easy_install -f %s -H None '
                           '<package>' % self.root)
            self.print_err('    pip install --no-index -f '
                           'file://%s <package>' % self.root)
        return 1


def main(argv=sys.argv, _basket_class=Basket):
    argv.pop(0)  # remove program name
    basket = _basket_class()
    if len(argv) == 0:
        return basket.syntax_error()
    command = argv.pop(0)
    if command in ('help', '--help', '-h'):
        basket.syntax_error(help=True)
        return 0
    if command == 'download':
        if len(argv) < 1:
            return basket.syntax_error('download')
        return basket.cmd_download(argv)
    if command == 'init':
        if len(argv) != 0:
            return basket.syntax_error('init')
        return basket.cmd_init()
    if command == 'list':
        return basket.cmd_list(argv)
    if command == 'prune':
        return basket.cmd_prune(argv)
    if command == 'update':
        return basket.cmd_update(argv)
    sys.exit(basket.syntax_error())


if __name__ == '__main__':
    main()
