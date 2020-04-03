import os
from lxml import etree
from .snapshot_release import snapshot_release_publication

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
    snapshot_release_publication(SNAPSHOT_TAG_SUFFIX, maven_get_version, maven_upload_assets)


if __name__ == "__main__":
    main()
