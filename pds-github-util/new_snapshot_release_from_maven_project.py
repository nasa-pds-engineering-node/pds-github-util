# Copyright 2019, California Institute of Technology ("Caltech").
# U.S. Government sponsorship acknowledged.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# * Redistributions must reproduce the above copyright notice, this list of
# conditions and the following disclaimer in the documentation and/or other
# materials provided with the distribution.
# * Neither the name of Caltech nor its operating division, the Jet Propulsion
# Laboratory, nor the names of its contributors may be used to endorse or
# promote products derived from this software without specific prior written
# permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import logging
import github3
# sudo apt-get install libxml2-dev libxslt-dev python-dev
# pip install lxml
import libxml2
import argparse

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def delete_snapshot_releases(_repo):
    """
        Delete all pre-existing snapshot releases
    """
    for release in _repo.releases():
        if release.tag_name.endswith('SNAPSHOT'):
            release.delete()


def create_snapshot_release(repo, repo_name, branch_name, tag_name, tagger):
    """
    Create a tag and new release from the latest commit on branch_name.
    Push the assets created in target directory.
    """
    our_branch = repo.branch(branch_name)
    repo.create_tag(tag_name,
                    f'nightly snapshot',
                    our_branch.commit.sha,
                    "commit",
                    tagger)

    # create the release
    release = repo.create_release(tag_name, target_commitish=branch_name, name=tag_name, body="nightly build")

    # upload assets
    targz_package = os.path.join(os.environ.get('GITHUB_WORKSPACE'),
                                 'target',
                                 f'{repo_name}-{tag_name}-bin.tar.gz')
    with open(targz_package, 'rb') as f_asset:
        release.upload_asset('application/tar+gzip',
                             f'{repo_name}-{tag_name}-bin.tar.gz',
                             f_asset)

    zip_package = os.path.join(os.environ.get('GITHUB_WORKSPACE'),
                               'target',
                               f'{repo_name}-{tag_name}-bin.zip')
    with open(zip_package, 'rb') as f_asset:
        release.upload_asset('application/zip',
                             f'{repo_name}-{tag_name}-bin.zip',
                             f_asset)


def main():
    """
    Script made to work in the context of a github action.
    """
    parser = argparse.ArgumentParser(description='Create new snapshot release')
    parser.add_argument('--token', dest='token',
                        help='github personal access token')
    args = parser.parse_args()

    # read organization and repository name
    repo_full_name = os.environ.get('GITHUB_REPOSITORY')
    repo_full_name_array = repo_full_name.split("/")
    org = repo_full_name_array[0]
    repo_name = repo_full_name_array[1]

    # read current version
    pom_path = os.path.join(os.environ.get('GITHUB_WORKSPACE'), 'pom.xml')
    doc = libxml2.parseFile(pom_path)
    ctxt = doc.xpathNewContext()
    ctxt.xpathRegisterNs("pom", "http://maven.apache.org/POM/4.0.0")
    tag_name = ctxt.xpathEval("/pom:project/pom:version")[0].content

    tagger = {"name": "thomas loubrieu",
              "email": "loubrieu@jpl.nasa.gov"}

    gh = github3.login(token=args.token)
    repo = gh.repository(org, repo_name)

    delete_snapshot_releases(repo)
    create_snapshot_release(repo, repo_name, "master", tag_name, tagger)


if __name__ == "__main__":
    main()
