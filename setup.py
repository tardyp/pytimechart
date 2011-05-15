#!/usr/bin/env python
"""Installs PyTimechart using setuptools

Run:
    python setup.py install
to install the package from the source archive.
"""
import os
from setuptools import setup, find_packages

version = [
    (line.split('=')[1]).strip().strip('"').strip("'")
    for line in open(os.path.join('timechart', 'window.py'))
    if line.startswith( '__version__' )
][0]

if __name__ == "__main__":
    extraArguments = {
        'classifiers': [
            """License :: OSI Approved :: BSD License""",
            """Programming Language :: Python""",
            """Topic :: Software Development :: Libraries :: Python Modules""",
            """Intended Audience :: Developers""",
        ],
        'keywords': 'gui,ftrace,perf,trace-event',
        'long_description' : """GUI Viewer for linux kernel traces

Provides explorability and overall visualization of linux kernel traces
""",
        'platforms': ['Any'],
    }
    ### Now the actual set up call
    setup (
        name = "pytimechart",
        version = version,
        url = "http://gitorious.org/pytimechart",
        download_url = "http://gitorious.org/pytimechart",
        description = "GUI Viewer for linux kernel traces",
        author = "Pierre Tardy",
        author_email = "tardyp@gmail.com",
        install_requires = [
            'Traits >= 3.0',
            'TraitsGUI >= 3.0',
            'TraitsBackendWX >= 3.0',
            'Enable >= 3.0',
            'Chaco >= 3.0',
        ],
        license = "BSD",
        namespace_packages = [
        'timechart',
        'timechart.plugins',
        'timechart.backends',
        ],
        packages = find_packages(exclude = [
        'examples',
        ]),
        package_data = {
            '': ['images/*'],
            },

        include_package_data = True,
        options = {
            'sdist':{
                'force_manifest':1,
                'formats':['gztar','zip'],},
        },
        zip_safe=False,
        entry_points = {
            'gui_scripts': [
                'pytimechart=timechart.timechart:main',
            ],
        },
        **extraArguments
    )

