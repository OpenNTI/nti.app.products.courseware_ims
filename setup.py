import codecs
from setuptools import setup, find_packages

VERSION = '0.0.0'

entry_points = {
	'console_scripts': [
		"nti_ims_enrollment = nti.app.products.courseware_ims.enroll:main",
	],
	"z3c.autoinclude.plugin": [
		'target = nti.app.products',
	],
}

setup(
	name = 'nti.app.products.courseware_ims',
	version = VERSION,
	author = 'Carlos Sanchez',
	author_email = 'carlos@nextthought.com',
	description = "Course-IMS Integration",
	long_description = codecs.open('README.rst', encoding='utf-8').read(),
	license = 'Proprietary',
	keywords = 'Course IMS',
	classifiers = [
		'Intended Audience :: Developers',
		'Natural Language :: English',
		'Operating System :: OS Independent',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.3',
		'Framework :: Pyramid',
	],
	packages=find_packages('src'),
	package_dir={'': 'src'},
	namespace_packages=['nti', 'nti.app', 'nti.app.products'],
	install_requires=[
		'setuptools',
		'nti.app.assessment',
		'nti.app.products.ims'
	],
	entry_points=entry_points
)
