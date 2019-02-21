# -*- coding: utf-8 -*-
{
    "name": """Gantt Native Report for Project""",
    "summary": """Added support Gantt""",
    "category": "Project",
    "images": ['static/description/icon.png'],
    "version": "11.18.3.16.1",
    "description": """
        PDF report

    """,
    "author": "Viktor Vorobjov",
    "license": "OPL-1",
    "website": "https://straga.github.io",
    "support": "vostraga@gmail.com",

    "depends": [
        "project",
        "project_native",
        "web_gantt_native",
    ],
    "external_dependencies": {"python": [], "bin": []},
    "data": [
        'report/project_native_views_main.xml',
        'report/project_native_report_templates.xml',
        'wizard/project_native_pdf_view.xml',
        # 'security/ir.model.access.csv',

    ],
    "qweb": [],
    "demo": [],

    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,
    "installable": True,
    "auto_install": False,
    "application": False,
}
