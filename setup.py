import codecs
from setuptools import setup, find_packages

entry_points = {
    'console_scripts': [
        "nti_ims_enrollment = nti.app.products.courseware_ims.scripts.nti_ims_enrollment:main",
    ],
    "z3c.autoinclude.plugin": [
        'target = nti.app.products',
    ],
}


def _read(fname):
    with codecs.open(fname, encoding='utf-8') as f:
        return f.read()


setup(
    name='nti.app.products.courseware_ims',
    version=_read('version.txt').strip(),
    author='Jason Madden',
    author_email='jason@nextthought.com',
    description="Course-IMS Integration",
    long_description=(_read('README.rst') + '\n\n' + _read('CHANGES.rst')),
    license='Apache',
    keywords='IMS courses',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Framework :: Zope',
        'Framework :: Pyramid',
    ],
    zip_safe=True,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    namespace_packages=['nti', 'nti.app', 'nti.app.products'],
    install_requires=[
        'setuptools',
        'nti.app.assessment',
        'nti.app.products.ims',
        'nti.app.products.courseware',
    ],
    entry_points=entry_points
)
