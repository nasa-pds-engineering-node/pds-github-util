📦 Installation
===============

This section describes how to install the PDS Github Util.


Requirements
------------

Prior to installing this software, ensure your system meets the following
requirements:

•  Python_ 3.6 or above. Python 2 will absolutely *not* work.
•  ``libxml2`` version 2.9.2; later 2.9 versions are fine.  Run ``xml2-config
   --version`` to find out.

Consult your operating system instructions or system administrator to install
the required packages. For those without system administrator access and are 
feeling anxious, you could try a local (home directory) Python_ 3 installation 
using a Miniconda_ installation.


Doing the Installation
----------------------

Install
^^^^^^^

The easiest way to install this software is to use Pip_, the Python Package
Installer. If you have Python on your system, you probably already have Pip;
you can run ``pip3 --help`` to check. Then run::

    pip3 install pds-github-util

If you don't want the package dependencies to interfere with your local system
you can also use a `virtual environment`_  for your deployment.
To do so::

    mkdir -p $HOME/.virtualenvs
    python3 -m venv $HOME/.virtualenvs/pds-github-util
    source $HOME/.virtualenvs/pds-doi-service/bin/activate
    pip3 install pds-github-util


Configure
^^^^^^^^^

Some environment variable need to be set (they are defined by default in github action but need to be set manually otherwise)::

    export GITHUB_WORKSPACE=<where the repository which we want to publish a snapshot is cloned>
    export GITHUB_REPOSITORY=<full name of the repository which we want to publish for example NASA-PDS-Incubator/pds-app-registry>


