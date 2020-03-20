# PDS utility function for github

Enforces the PDS engineering node software lifecycle

# Prerequisites

libxml2 is used. It needs to be deployed as follow:

## Macos

    brew install libxml2
    cd ./venv/lib/python3.7/site-packages/  # chose the site package of the used python
    ln -s /usr/local/Cellar/libxml2/2.9.10/lib/python3.7/site-packages/* .

## Ubuntu

    sudo apt-get install libxml2-dev libxslt-dev python-dev
    pip install lxml

# deploy and run

Deploy:

    pip install pds-gihub-util

Some environment variable need to be set (they are defined by default in github action but need to be set manually otherwise)

    export GITHUB_WORKSPACE=<where the repository which we want to publish a snapshot is cloned>
    export GITHUB_REPOSITORY=<full name of the repository which we want to publish for example NASA-PDS-Incubator/pds-app-registry>

Run with, as parameter, the personal access token for github:

    snapshot-release --token <personal access token>


# Development
 
    git clone ...
    cd pds-github-util
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    
Update the code

Create package and publish it:

Set the version in setup.py

Tag the code

    git tag <version>
    git push origin --tags

Create the package:

    python setup.py sdist

Publish it as a github release.

Publish on pypi (you need a pypi account):

    pip install twine
    twine upload dist/*
    
    
    