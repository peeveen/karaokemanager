from setuptools import setup, find_packages
from karaokemanager.karaoke_manager import KaraokeManager

with open('README.md') as readme_file:
    README = readme_file.read()

with open('HISTORY.md') as history_file:
    HISTORY = history_file.read()

setup_args = dict(
	name='karaokemanager',
	version=KaraokeManager.VERSION,
	description='Karaoke session management utility',
	long_description_content_type="text/markdown",
	long_description=README + '\n\n' + HISTORY,
	license='MIT',
	packages=find_packages(),
	entry_points={
		"console_scripts": [
				"karaokemanager=karaokemanager.__main__:main",
		]
	},
	include_package_data=True,
	author='Steven Frew',
	author_email='steven.fullhouse@gmail.com',
	keywords=['karaokemanager', 'karaoke'],
	url='https://github.com/peeveen/karaokemanager',
	download_url='https://pypi.org/project/karaokemanager/'
)

install_requires = ['colorama', 'pyyaml', 'textdistance']

if __name__ == '__main__':
    setup(**setup_args, install_requires=install_requires)