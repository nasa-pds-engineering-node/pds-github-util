import os
from lxml import etree
from .snapshot_release import snapshot_release_publication


SNAPSHOT_TAG_SUFFIX = "SNAPSHOT"


def maven_get_version():
    # read current version
    pom_path = os.path.join(os.environ.get('GITHUB_WORKSPACE'), 'pom.xml')
    pom_doc = etree.parse(pom_path)
    r = pom_doc.xpath('/pom:project/pom:version',
        namespaces = {'pom': 'http://maven.apache.org/POM/4.0.0'})
    return r[0].text


def main():
    snapshot_release_publication(SNAPSHOT_TAG_SUFFIX, maven_get_version)


if __name__ == "__main__":
    main()
