from setuptools import setup, find_packages

setup(
    name='secucam',
    author='Arne Beer',
    author_email='arne@twobeer.de',
    version='0.1.0',
    description='A nice setup for home surveillance.',
    keywords='surveillance security home server telegram bot',
    url='http://github.com/nukesor/pueue',
    license='MIT',
    install_requires=[
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Environment :: Console'
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'secucam=secucam:main'
        ]
    })
