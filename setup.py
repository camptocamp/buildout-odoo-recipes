from setuptools import setup

setup(
    name = "openerp_auto_run",
    entry_points = {
        'zc.buildout': ['auto-run = openerp_auto_run:OpenERPAutoRun']
    },
)
