import os
import shutil

from basket.tests.shelltest import find_shell_sessions


def test_docs():
    here = os.path.dirname(__file__)
    basket_root = os.path.join(here, '.basket-test')
    os.environ['BASKET_ROOT'] = basket_root
    readme_path = os.path.join(here, '..', '..', 'README.rst')
    try:
        with open(readme_path) as readme:
            for session in find_shell_sessions(readme):
                # Ignore 'pip' and 'easy_install' command that would
                # install packages in our development environment.
                if session.cmd.startswith(('pip', 'easy_install')):
                    continue
                # Also ignore 'basket help': the doc has additional
                # newlines that make it hard to test.
                if session.cmd.startswith('basket help'):
                    continue
                session.replace('~/.basket', basket_root)
                yield session.validate
    finally:
        shutil.rmtree(basket_root)

# Running this test is very long. Disable by default.
if not os.environ.get('WITH_SHELLTESTS'):
    test_docs = None
