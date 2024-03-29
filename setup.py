from setuptools import setup


setup(
    name='statify',
    version='1.3.0',
    packages=[
        'statify',
        'statify.webserver',
    ],
    package_data={
        'statify.webserver': ['static/*', 'templates/*'],
    },
    entry_points={
        'console_scripts': [
            'statify=statify.statify:main',
            'statify_webserver=statify.webserver.webserver:main'
        ]
    },
    description="Pull your playlist and listening data from the Spotify API",
    author='@foobuzz',
    author_email='foobuzz@fastmail.com',
    url='https://github.com/foobuzz/statify',
    install_requires=[
        'pypika==0.35.14',
        'pyyaml==5.3.1',
        'setuptools==49.1.0',
        'spotipy==2.16.0',
        'flask==2.1.2',
    ],
    extras_require={
        'tests': {
            'flake8==3.8.4',
            'pytest==5.4.3',
            'pytest-flask==1.2.0',
            'pytest-mock==3.1.1',
            'pyfakefs==4.0.2',
            'responses==0.10.15',
        },
    },
)
