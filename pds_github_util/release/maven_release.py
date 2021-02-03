import fnmatch
import os
from lxml import etree
from .release import release_publication

SNAPSHOT_TAG_SUFFIX = "SNAPSHOT"


def maven_get_version():
    # read current version
    pom_path = os.path.join(os.environ.get('GITHUB_WORKSPACE'), 'pom.xml')
    pom_doc = etree.parse(pom_path)
    r = pom_doc.xpath('/pom:project/pom:version',
                      namespaces={'pom': 'http://maven.apache.org/POM/4.0.0'})
    return r[0].text


def maven_upload_assets(repo_name, tag_name, release):
    """
          Upload packages produced by maven

    """
    # upload assets
    assets = ['*-bin.tar.gz', '*-bin.zip', '*.jar']
    for dirname, subdirs, files in os.walk(os.environ.get('GITHUB_WORKSPACE')):
        if dirname.endswith('target'):
            for extension in assets:
                for filename in fnmatch.filter(files, extension):
                    with open(os.path.join(dirname, filename), 'rb') as f_asset:
                        release.upload_asset('application/tar+gzip',
                                             filename,
                                             f_asset)


def main():
    release_publication(SNAPSHOT_TAG_SUFFIX, maven_get_version, maven_upload_assets)


if __name__ == "__main__":
    main()
