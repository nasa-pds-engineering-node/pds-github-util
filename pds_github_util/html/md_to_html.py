import os
from markdown2 import Markdown
from pystache import Renderer
import emoji

def md_to_html(in_file, out_file,
               template_kargs):
    with open(in_file, 'r') as f_in:
        markdowner = Markdown()
        html_str = markdowner.convert(f_in.read())
        html_emojized_str = emoji.emojize(html_str, use_aliases=True)
        template_kargs['requirements_html'] = html_emojized_str
    renderer = Renderer()
    template_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'REQUIREMENTS.html.template')
    with open(out_file, 'w') as f_out:
        html_str = renderer.render_path(template_file, template_kargs)
        f_out.write(html_str)
    return out_file

