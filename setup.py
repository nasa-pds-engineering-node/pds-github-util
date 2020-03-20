import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pds_github_util", # Replace with your own username
    version="0.0.1",
    license="apache-2.0",
    author="thomas loubrieu",
    author_email="loubrieu@jpl.nasa.gov",
    description="util functions for software life cycle enforcement on github",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NASA-PDS-Incubator/pds-github-util",
    packages=setuptools.find_packages(),
    keywords=['github', 'action', 'github action', 'snapshot', 'release', 'maven'],

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'github3.py>=1.3',
        'libxml2-python>=2.9'
    ],
    entry_points={
        'console_scripts': ['snapshot-release=pds_github_util:snapshot_release.main'],
    }

)