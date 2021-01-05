"""
生成模板
"""

from .spider import ResourceRoot


def render_template(template: str, data: dict):
    return template.format(**data)


def init(dirname: str, name: str, template_style: int):
    """初始化项目"""
    template_root = ResourceRoot('templates')
    dir_root = ResourceRoot(dirname)

    template_root.close()
    dir_root.close()
