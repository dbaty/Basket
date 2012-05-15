from types import ModuleType
from unittest import TestCase


class TestGetPackageName(TestCase):

    def call_fut(self, line):
        from basket.main import get_package_name
        return get_package_name(line)

    def test_it(self):
        self.assertEqual(self.call_fut('foo'), 'foo')
        self.assertEqual(self.call_fut('foo==1.2a'), 'foo')
        # I am not sure that spaces are allowed but just in case...
        self.assertEqual(self.call_fut('foo == 1.2'), 'foo')
        self.assertEqual(self.call_fut('foo>=1.2'), 'foo')
        self.assertEqual(self.call_fut('foo>1.2'), 'foo')
        self.assertEqual(self.call_fut('foo<=1.2'), 'foo')
        self.assertEqual(self.call_fut('foo<1.2'), 'foo')
        self.assertEqual(self.call_fut('foo==1.2'), 'foo')


class TestGetNameAndVersion(TestCase):

    def call_fut(self, filename):
        from basket.main import get_name_and_version
        return get_name_and_version(filename)

    def test_it(self):
        self.assertEqual(self.call_fut('foo-1.2.tar.gz'),
                         {'name': 'foo', 'version': '1.2'})
        self.assertEqual(self.call_fut('foo-1.2.zip'),
                         {'name': 'foo', 'version': '1.2'})
        self.assertEqual(self.call_fut('foo-1.2.egg'),
                         {'name': 'foo', 'version': '1.2'})
        self.assertEqual(self.call_fut('foo-bar-1.2.zip'),
                         {'name': 'foo-bar', 'version': '1.2'})
        self.assertEqual(self.call_fut('foo-bar-1.2.tar.bz2'),
                         {'name': 'foo-bar', 'version': '1.2'})


class TestBasket(TestCase):

    def _make_one(self):
        from basket.main import Basket
        return Basket()

    def test_client_property(self):
        basket = self._make_one()
        first_access = basket.client
        next_access = basket.client
        self.assertTrue(first_access is next_access)

    def test_download_packages(self):
        basket = self._make_one()
        class FakeOs(object):
            def __init__(self, subdirs):
                self.subdirs = subdirs
            def listdir(self, dir):
                return self.subdirs
        basket.os = FakeOs(['Foo-1.2.tar.gz', 'Bar-1.0.tar.bz2'])
        expected = [{'filename': 'Foo-1.2.tar.gz',
                     'name': 'Foo',
                     'version': '1.2'},
                    {'filename': 'Bar-1.0.tar.bz2',
                     'name': 'Bar',
                     'version': '1.0'}]
        self.assertEqual(basket.downloaded_packages, expected)

    def test_find_package_name(self):
        basket = self._make_one()
        results = [{'name': 'Foosomething', 'version': '1.0'},
                   {'name': 'Foo', 'version': '2.0'},
                   {'name': 'Foo', 'version': '1.0'}]
        basket._client = Mock(search=results)
        self.assertEqual(basket._find_package_name('Foo'),
                         {'name': 'Foo', 'version': '2.0'})

    def test_find_package_name_package_not_found(self):
        basket = self._make_one()
        results = [{'name': 'Foosomething', 'version': '2.0'}]
        basket._client = Mock(search=results)
        self.assertEqual(basket._find_package_name('Foo'), None)

    def test_find_package_url(self):
        basket = self._make_one()
        results = [{'python_version': 'egg', 'url': 'url-of-egg'},
                   {'python_version': 'source', 'url': 'url-of-source-version'}]
        basket._client = Mock(release_urls=results)
        self.assertEqual(basket._find_package_url('Foo', '1.0'),
                         'url-of-source-version')

    def test_find_package_url_package_not_found(self):
        basket = self._make_one()
        results = [{'python_version': 'egg', 'url': 'url-of-egg'}]
        basket._client = Mock(release_urls=results)
        self.assertEqual(basket._find_package_url('Foo', '1.0'), None)

    def test_find_requirements_tar_file(self):
        class FakeTarfile(object):
            def is_tarfile(self, path):
                return True
        basket = self._make_one()
        basket.tarfile = FakeTarfile()
        requirements = ['Foo>=1.2', 'Bar', '[test]', 'nose']
        basket._get_requirements_from_tar_archive = lambda path: requirements
        self.assertEqual(basket._find_requirements('path.tar.gz'),
                         ['Foo', 'Bar', 'nose'])

    def test_find_requirements_zip_file(self):
        class FakeTarfile(object):
            def is_tarfile(self, path):
                return False
        class FakeZipfile(object):
            def is_zipfile(self, path):
                return True
        basket = self._make_one()
        basket.tarfile = FakeTarfile()
        basket.zipfile = FakeZipfile()
        requirements = ['Foo>=1.2', 'Bar', '[test]', 'nose']
        basket._get_requirements_from_zip_archive = lambda path: requirements
        self.assertEqual(basket._find_requirements('path.zip'),
                         ['Foo', 'Bar', 'nose'])

    def test_find_requirements_unknown_archive_format(self):
        import os
        class FakeTarOrZipfile(object):
            def is_tarfile(self, path):
                return False
            def is_zipfile(self, path):
                return False
        basket = self._make_one()
        basket.tarfile = FakeTarOrZipfile()
        basket.zipfile = FakeTarOrZipfile()
        basket.err = DummyStream()
        requirements = ['Foo>=1.2', 'Bar', '[test]', 'nose']
        basket._get_requirements_from_zip_archive = lambda path: requirements
        self.assertEqual(basket._find_requirements('path.zip'), ())
        self.assertEqual(basket.err.stream,
                         'Could not open "path.zip" (unknown archive '
                         'format).' + os.linesep)

    def test_has_packages(self):
        basket = self._make_one()
        basket._downloaded_packages = [{'name': 'Foo', 'version': '1.0'}]
        self.assertTrue(basket._has_package('Foo', '1.0'))
        self.assertFalse(basket._has_package('Foo', '2.0'))
        self.assertFalse(basket._has_package('Bar', '1.0'))

    def test_download(self):
        import os
        package = 'Foo'
        version = '1.0'
        url = 'http://example.com/Foo-1.0.tar.gz'
        basket = self._make_one()
        basket.root = '/path/of/basket/root'
        basket.urllib = Mock(urlretrieve='data')
        basket._downloaded_packages = []
        target_path = os.path.join(basket.root, 'Foo-1.0.tar.gz')
        self.assertEqual(basket._download(package, version, url),
                         target_path)
        self.assertEqual(basket._downloaded_packages,
                         [{'name': package, 'version': version}])
        self.assertEqual(basket.urllib.called,
                         [('urlretrieve', (url, target_path), {}), ])

    def test_print_msg(self):
        import os
        basket = self._make_one()
        basket.out = DummyStream()
        data = 'This is a message.'
        basket.print_msg(data)
        self.assertEqual(basket.out.stream, data + os.linesep)

    def test_print_err(self):
        import os
        basket = self._make_one()
        basket.err = DummyStream()
        data = 'This is a message.'
        basket.print_err(data)
        self.assertEqual(basket.err.stream, data + os.linesep)

    def test_cmd_list_all_packages(self):
        import os
        basket = self._make_one()
        basket._downloaded_packages = [{'name': 'Foo', 'version': '1.0'},
                                       {'name': 'Foo', 'version': '2.0'}]
        basket.out = DummyStream()
        self.assertEqual(basket.cmd_list(), 0)
        self.assertEqual(basket.out.stream,
                         'Foo 1.0' + os.linesep + 'Foo 2.0' + os.linesep)

    def test_cmd_list_specific_packages(self):
        import os
        basket = self._make_one()
        basket._downloaded_packages = [{'name': 'Foo', 'version': '1.0'},
                                       {'name': 'Foo', 'version': '2.0'}]
        basket.out = DummyStream()
        basket.err = DummyStream()
        self.assertEqual(basket.cmd_list(('Foo', 'Bar')), 0)
        self.assertEqual(basket.out.stream,
                         'Foo 1.0' + os.linesep + 'Foo 2.0' + os.linesep)
        self.assertEqual(basket.err.stream,
                         'Package "bar" is not installed (or it is there but '
                         'you mistyped the package name).' + os.linesep)

    def test_cmd_download_unknown_package(self):
        import os
        basket = self._make_one()
        basket.err = DummyStream()
        basket._client = Mock(search=())
        self.assertEqual(basket.cmd_download(('Foo', )), 0)
        self.assertEqual(basket.err.stream,
                         'Could not find any package named "Foo".' + os.linesep)

    def test_cmd_download_already_up_to_date(self):
        import os
        basket = self._make_one()
        basket.out = DummyStream()
        basket._client = Mock(search=[{'name': 'Foo', 'version': '1.0'}],
                              release_urls=[])
        basket._downloaded_packages = [{'name': 'Foo', 'version': '1.0'}]
        self.assertEqual(basket.cmd_download(('Foo', )), 0)
        self.assertEqual(basket.out.stream,
                         'Foo is already up to date (1.0).' + os.linesep)

    def test_cmd_download_no_suitable_distribution(self):
        import os
        basket = self._make_one()
        basket.err = DummyStream()
        basket._client = Mock(search=[{'name': 'Foo', 'version': '1.0'}],
                              release_urls=[])
        basket._downloaded_packages = []
        self.assertEqual(basket.cmd_download(('Foo', )), 0)
        self.assertEqual(basket.err.stream,
                         'Could not find a suitable distribution for '
                         'Foo 1.0.' + os.linesep)

    def test_cmd_download_success(self):
        import os
        basket = self._make_one()
        basket._downloaded_packages = []
        basket.urllib = Mock(urlretrieve='data')
        basket.out = DummyStream()
        def release_urls(package, version):
            url = 'http://example.com/%s-%s.tar.gz' % (package, version)
            return [{'python_version': 'source', 'url': url}]
        basket._client = Mock(search=[{'name': 'Foo', 'version': '1.0'},
                                      {'name': 'Bar', 'version': '2.0'}],
                              release_urls=release_urls)
        # Fake requirements: Foo requires Bar. Bar does not require anything.
        basket._find_requirements = lambda path: 'Foo' in path and ['Bar'] or []
        self.assertEqual(basket.cmd_download(('Foo', )), 0)
        self.assertEqual(basket.out.stream,
                         'Added Foo 1.0.{0}'
                         '  -> requires: Bar{0}' 
                         'Added Bar 2.0.{0}'.format(os.linesep))

    def test_cmd_prune_unknown_package(self):
        import os
        basket = self._make_one()
        basket.os = Mock(remove=lambda: 1)
        basket.err = DummyStream()
        basket._downloaded_packages = []
        self.assertEqual(basket.cmd_prune(('Foo', )), 0)
        self.assertEqual(basket.err.stream,
                         'Package "foo" is not installed (or it is there '
                         'but you mistyped the package name).' + os.linesep)

    def test_cmd_prune_package_with_only_one_version(self):
        import os
        basket = self._make_one()
        basket.os = Mock(remove=lambda: 1)  # safety belt
        basket.out = DummyStream()
        basket._downloaded_packages = [{'name': 'Foo', 'version': '1.0'}]
        self.assertEqual(basket.cmd_prune(('Foo', )), 0)
        self.assertEqual(basket.out.stream,
                         'Foo has only one version. '
                         'Nothing to prune.' + os.linesep)

    def test_cmd_prune_specific_package(self):
        import os
        basket = self._make_one()
        basket.os = Mock(remove=lambda path: 1, path=os.path)  # safety belt
        basket.os.path
        basket.out = DummyStream()
        basket._downloaded_packages = [{'name': 'Foo', 'version': '1.0',
                                        'filename': '/belt/and/suspenders'},
                                       {'name': 'Foo', 'version': '2.0'}]
        self.assertEqual(basket.cmd_prune(('Foo', )), 0)
        self.assertEqual(basket.out.stream,
                         'Removed Foo 1.0 (kept 2.0).' + os.linesep)

    def test_cmd_prune_all(self):
        import os
        basket = self._make_one()
        basket.os = Mock(remove=lambda path: 1, path=os.path)  # safety belt
        basket.os.path
        basket.out = DummyStream()
        basket._downloaded_packages = [{'name': 'Foo', 'version': '1.0',
                                        'filename': '/belt/and/suspenders'},
                                       {'name': 'Foo', 'version': '2.0'}]
        self.assertEqual(basket.cmd_prune(()), 0)
        self.assertEqual(basket.out.stream,
                         'Removed Foo 1.0 (kept 2.0).' + os.linesep)

    def test_cmd_update_all(self):
        basket = self._make_one()
        basket._downloaded_packages = [{'name': 'Foo'}, {'name': 'Bar'}]
        basket.cmd_download = lambda args: args
        self.assertEqual(basket.cmd_update(), ['Foo', 'Bar'])

    def test_cmd_update_specific_packages(self):
        basket = self._make_one()
        basket._downloaded_packages = [{'name': 'Foo'}, {'name': 'Bar'}]
        basket.cmd_download = lambda packages: packages
        self.assertEqual(basket.cmd_update(('Foo', )), ('Foo', ))


class DummyStream(object):

    def __init__(self):
        self.stream = ''

    def write(self, data):
        self.stream += data

class Mock(object):
    def __init__(self, **expectations):
        self.expectations = expectations.copy()
        self.accessed = 0
        self.called = []

    def __getattr__(self, attr):
        mock = self.expectations[attr]
        if type(mock) is ModuleType:
            return mock
        def wrapper(*args, **kwargs):
            self.called.append((attr, args, kwargs))
            if callable(mock):
                return mock(*args, **kwargs)
            else:
                return mock
        return wrapper
