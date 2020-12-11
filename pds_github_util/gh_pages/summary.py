import os
import logging
from pds_github_util.tags.tags import Tags
from pds_github_util.corral.herd import Herd
from rstcloth import RstCloth
from uuid import uuid4

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COLUMNS = ['manual', 'changelog', 'requirements', 'download', 'license', 'feedback']

def _indent(content, indent):
    """
    :param content:
    :param indent:
    :return:
    """
    if indent == 0:
        return content
    else:
        indent = " " * indent
        if isinstance(content, list):
            return ["".join([indent, line]) for line in content]
        else:
            return "".join([indent, content])


class RstClothReferenceable(RstCloth):
    def __init__(self, line_width=72):
        super().__init__(line_width=line_width)
        self._deffered_directives = []

    def hyperlink(self, ref, url):
        self._deffered_directives.append(f".. _{ref}: {url}")

    def deffered_directive(self, name, arg=None, fields=None, content=None, indent=0, wrap=True, reference=None):
        """
        :param name: the directive itself to use
        :param arg: the argument to pass into the directive
        :param fields: fields to append as children underneath the directive
        :param content: the text to write into this element
        :param indent: (optional default=0) number of characters to indent this element
        :param wrap: (optional, default=True) Whether or not to wrap lines to the line_width
        :param reference: (optional, default=None) Reference to call the directive elswhere
        :return:
        """
        logger.debug("Ignoring wrap parameter, presumably for api consistency. wrap=%s", wrap)
        o = list()
        if reference:
            o.append(".. |{0}| {1}::".format(reference, name))
        else:
            o.append(".. {0}::".format(name))

        if arg is not None:
            o[0] += " " + arg

        if fields is not None:
            for k, v in fields:
                o.append(_indent(":" + k + ": " + str(v), 3))

        if content is not None:
            o.append("")

            if isinstance(content, list):
                o.extend(_indent(content, 3))
            else:
                o.append(_indent(content, 3))

        self._deffered_directives.extend(_indent(o, indent))

    def write(self, filename):
        """
            :param filename:
            :return:
            """
        dirpath = os.path.dirname(filename)
        if os.path.isdir(dirpath) is False:
          try:
              os.makedirs(dirpath)
          except OSError:
              logger.info("{0} exists. ignoring.".format(dirpath))

        with open(filename, "w") as f:
          f.write("\n".join(self._data))
          f.write("\n")
          f.write("\n".join(self._deffered_directives))
          f.write("\n")


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
        column_headers.append(f'|{column}|')

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


def write_rst_file(herd, output_file_name, version):

    d = RstClothReferenceable()
    d.title(f'Software Summary (build {version})')

    data = []
    for k, ch in herd.get_cattle_heads().items():
        ch.set_rst(d)
        data.append(ch.get_table_row(format='rst'))

    d.table(
        get_table_columns_rst(),
        data=data
    )

    rst_column_header_images(d)

    logger.info(f'Create file {output_file_name}.rst')
    d.write(f'{output_file_name}.rst')



def write_build_summary(gitmodules=None, root_dir='.', output_file_name=None, token=None, dev=False, version=None, format='md'):

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
