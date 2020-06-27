import re
import setuptools

with open("./pds_github_util/__init__.py") as fi:
    result = re.search(r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fi.read())
version = result.group(1)

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt', 'r') as f:
    pip_requirements = f.readlines()

setuptools.setup(
    name="pds_github_util", # Replace with your own package name
    version=version,
    license="apache-2.0",
    author="thomas loubrieu",
    author_email="loubrieu@jpl.nasa.gov",
    description="util functions for software life cycle enforcement on github",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NASA-PDS/pds-github-util",
    download_url = "https://github.com/NASA-PDS/pds-github-util/releases/download/0.0.1/pds_github_util-0.0.1.tar.gz",
    packages=setuptools.find_packages(),
    include_package_data=True,
    package_data = {
        '' : ['*.template', 'gh_pages/resources/*']},
    keywords=['github', 'action', 'github action', 'snapshot', 'release', 'maven'],

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=pip_requirements,
    entry_points={
        # snapshot-release for backward compatibility
        'console_scripts': ['snapshot-release=pds_github_util.release.maven_snapshot_release:main',
                            'maven-snapshot-release=pds_github_util.release.maven_snapshot_release:main',
                            'python-snapshot-release=pds_github_util.release.python_snapshot_release:main',
                            'requirement-report=pds_github_util.requirements.generate_requirements:main',
                            'git-ping=pds_github_util.branches.git_ping:main',
                            'summaries=pds_github_util.gh_pages.build_summaries:main'
                            ],
    },


)