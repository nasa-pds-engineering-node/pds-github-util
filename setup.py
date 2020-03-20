import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pds-github-util", # Replace with your own username
    version="0.0.1",
    author="PDS-NASA",
    author_email="pds@jpl.nasa.gov",
    description="util functions for software life cycle enforcement on github",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'github3.py>=1.3',
        'libxml2-python>=2.9'
    ]

)