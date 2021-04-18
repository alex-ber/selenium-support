import os

import setuptools
from setuptools import setup


#VERSION should be defined before importing UploadCommand
VERSION = '0.0.1'
from alexber.utils import UploadCommand
NAME = 'selenium_support'
SHORT_NAME = 'seleniumsupport'
VCS_URL = 'https://github.com/alex-ber/selenium-support'
DESCRIPTION = 'Usefull function for Selenium umbrella project'
AUTHOR = 'Alexander Berkovich'


base_dir = os.path.dirname(os.path.realpath(__file__))

def get_content(filename):
    with open(os.path.join(base_dir, filename)) as f:
        content = f.read().splitlines()
    return content

install_requires = get_content('requirements.txt')
tests_require = get_content('requirements-tests.txt')

extras = {
    'tests': tests_require
}

lnk_data = os.path.join('alexber', SHORT_NAME, 'data')



try:
    try:
        os.unlink(lnk_data)
    except OSError:
        pass

    os.symlink(os.path.join('..', '..', 'data'), lnk_data)

    setup(
        name=NAME,
        version=VERSION,
        url=VCS_URL,
        author=AUTHOR,
        description=DESCRIPTION,
        long_description="\n\n".join([
            open(os.path.join(base_dir, "README.md"), "r").read(),
            open(os.path.join(base_dir, "CHANGELOG.md"), "r").read()
        ]),
        long_description_content_type="text/markdown",
        packages=setuptools.find_packages(exclude=('tests', 'tests.*', 'data')),
        # see https://stackoverflow.com/a/26533921
        # see also https://stackoverflow.com/questions/24347450/how-do-you-add-additional-files-to-a-wheel
        # data_files=[(f'Lib/site-packages/alexber/{SHORT_NAME}', ['data/config.yml', 'data/requirements-src.txt',
        #                                                    'data/driver.py']),
        #             #(f'lib/python3.7/site-packages/alexber/{SHORT_NAME}', ['requirements-src.txt'])
        #             ],
        # package_data={'alexber.{SHORT_NAME}': ['data/*', 'data/config.yml',
        #                                   'data/requirements-stc.txt', 'data/requirements-dest.txt']},
        package_data={f'alexber.{SHORT_NAME}': ['data/*'
                                                ]},
        include_package_data=True,
        install_requires=install_requires,
        # entry_points={"console_scripts": [
        #     f"python-{SHORT_NAME}-tool=alexber.{SHORT_NAME}.data.__main__:main"
        # ]},
        # $ setup.py publish support.
        # python3 setup.py upload
        cmdclass={
            'upload': UploadCommand,
        },
        extras_require=extras,
        test_suite="tests",
        tests_require=tests_require,
        setup_requires=['pytest-runner'],
        namespace_packages=('alexber',),
        license='Apache 2.0',
        keywords='Selenium support BMP browsermobproxy web_driver driver Chrome Firefox har download  ' \
                 'wait wait_page_loaded click click_sync wait_chrome_file_finished_downloades wait_for_display',
        classifiers=[
            # See: https://pypi.python.org/pypi?:action=list_classifiers
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'Intended Audience :: Education',
            'License :: OSI Approved :: BSD License',

            # List of python versions and their support status:
            # https://en.wikipedia.org/wiki/CPython#Version_history
            'Programming Language :: Python',
            'Programming Language :: Python :: 3 :: Only',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: Implementation :: CPython',
            "Topic :: Utilities",
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Topic :: Desktop Environment',
            'Topic :: Education',
            'Operating System :: OS Independent',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX',
            'Operating System :: Unix',
            'Natural Language :: English',
        ],
        python_requires='>=3.8',
        zip_safe=False,

    )

finally:
    try:
        os.unlink(lnk_data)
    except OSError:
        pass




