import os
import logging
from pds_github_util.tags.tags import Tags
from pds_github_util.utils import RstClothReferenceable
from pds_github_util.corral.herd import Herd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COLUMNS = ['manual', 'changelog', 'requirements', 'download', 'license', 'feedback']

REPO_TYPES = {
    'tool': {
        'title': 'Standalone Tools and Libraries',
        'description': 'PDS tools for discipline nodes, data providers and users.'
    },
    'service': {
        'title': 'Discipline Node Services',
        'description': 'PDS servers that Discipline Node should deploy to publish their archive at PDS level'
    },
    'library': {
        'title': 'Libraries',
        'description': 'Libraries supported by PDS'
    },
    'core': {
        'title': 'Engineering Node Services',
        'description': 'PDS servers deployed by PDS Engineering Node at central level'
    },
    'other': {
        'title': 'Other Tools and Libraries (dependencies)',
        'description': 'Other software assets re-used in previously listed applications'
    },
    'unknown': {
        'title': 'Additional software assets',
        'description': ''
    }
}


def get_table_columns_md():

    def column_header(column):
        return f'![{column}](https://nasa-pds.github.io/pdsen-corral/images/{column}_text.png)'

    column_headers = []
    for column in COLUMNS:
        column_headers.append(column_header(column))

    return ["tool", "version", "last updated", "description", *column_headers]


def get_table_columns_rst():


    column_headers = []
    for column in COLUMNS:
        column_headers.append(f'l |{column}|')

    return ["tool", "version", "last updated", "description", *column_headers]




def rst_column_header_images(d):

    for column in COLUMNS:
        d.deffered_directive('image', arg=f'https://nasa-pds.github.io/pdsen-corral/images/{column}_text.png', fields=[('alt', column)], reference=column)




def write_md_file(herd, output_file_name, version):
    from mdutils import MdUtils

    software_summary_md = MdUtils(file_name=output_file_name, title=f'Software Summary (build {version})')

    table = get_table_columns_md()
    n_columns = len(table)
    for k, ch in herd.get_cattle_heads().items():
        table.extend(ch.get_table_row(format='md'))
    software_summary_md.new_table(columns=n_columns,
                                  rows=herd.number_of_heads() + 1,
                                  text=table,
                                  text_align='center')

    logger.info(f'Create file {output_file_name}.md')
    software_summary_md.create_md_file()


def write_rst_introduction(d: RstClothReferenceable, version: str):
    d.title(f'Software Catalog (build {version})')

    d.content(f'The software provided for the build {version} are listed hereafter and organized by category:')
    d.newline()
    for t, section in REPO_TYPES.items():
        if t != 'unknown':
            d.li(f"`{section['title']}`_")
            d.newline()

def write_rst_file(herd, output_file_name, version):

    d = RstClothReferenceable()

    write_rst_introduction(d, version)

    # create one section per type of repo
    data = {t: [] for t in REPO_TYPES}
    for k, ch in herd.get_cattle_heads().items():
        ch.set_rst(d)
        if ch.type in REPO_TYPES.keys():
            data[ch.type].append(ch.get_table_row(format='rst'))
        else:
            logger.warning("unknown type for repo %s in build version %s", ch.repo_name, version)
            data['unknown'].append(ch.get_table_row(format='rst'))

    for type, type_data in data.items():
        if type_data:
            d.h1(REPO_TYPES[type]['title'])
            d.content(REPO_TYPES[type]['description'])
            d.table(
                get_table_columns_rst(),
                data=type_data
            )

    rst_column_header_images(d)

    logger.info(f'Create file {output_file_name}.rst')
    d.write(f'{output_file_name}.rst')



def write_build_summary(
        gitmodules=None,
        root_dir='.',
        output_file_name=None,
        token=None,
        dev=False,
        version=None,
        format='md'):

    herd = Herd(gitmodules=gitmodules, dev=dev, token=token)

    if version is None:
        version = herd.get_shepard_version()
    else:
        # for unit test
        herd.set_shepard_version(version)

    logger.info(f'build version is {version}')
    is_dev = Tags.JAVA_DEV_SUFFIX in version or Tags.PYTHON_DEV_SUFFIX in version
    if dev and not is_dev:
        logger.error(f'version of build does not contain {Tags.JAVA_DEV_SUFFIX} or {Tags.PYTHON_DEV_SUFFIX}, dev build summary is not generated')
        exit(1)
    elif not dev and is_dev:
        logger.error(f'version of build contains {Tags.JAVA_DEV_SUFFIX} or {Tags.PYTHON_DEV_SUFFIX}, release build summary is not generated')
        exit(1)

    if not output_file_name:
        output_file_name = os.path.join(root_dir, version, 'index')
    os.makedirs(os.path.dirname(output_file_name), exist_ok=True)

    if format == 'md':
        write_md_file(herd, output_file_name, version)
    elif format == 'rst':
        write_rst_file(herd, output_file_name, version)

    return herd
