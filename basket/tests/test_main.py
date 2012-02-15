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
