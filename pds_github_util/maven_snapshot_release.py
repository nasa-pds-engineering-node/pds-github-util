import os
import libxml2
from .snapshot_release import snapshot_release_publication


SNAPSHOT_TAG_SUFFIX = "SNAPSHOT"


def maven_get_version():
    # read current version
    pom_path = os.path.join(os.environ.get('GITHUB_WORKSPACE'), 'pom.xml')
    doc = libxml2.parseFile(pom_path)
    ctxt = doc.xpathNewContext()
    ctxt.xpathRegisterNs("pom", "http://maven.apache.org/POM/4.0.0")
    return ctxt.xpathEval("/pom:project/pom:version")[0].content


main = snapshot_release_publication(SNAPSHOT_TAG_SUFFIX, maven_get_version)

if __name__ == "__main__":
    main()
