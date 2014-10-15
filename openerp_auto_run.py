import os
import stat
import shutil
import logging
from string import Template
import zc.buildout
AUTORUNDIR = 'auto-run'
AUTORUNSCRIPT = 'autorun.sh'
TEMPLATENAME = 'autorun.sh.in'
SUPERVISORDAEMON = 'supervisord'
BINPATH = 'bin'


class OpenERPAutoRun:
    """Initialize auto-run script and symlink
    to be used by openerp-multi-instance script.

    To use the receip to add in buidlout section: ::
       develop = openerp_recipes/openerp_auto_run/
    then create a section like that: ::

        [openerp_auto_run]
        recipe = openerp_auto_run:auto-run
        start_on_boot = yes

    and add it to you part

    The recipe will generate an autorun.sh script in /bin/.
    The script will map the call made by init script to supervisor.
    The recipe will create the auto-run folder
    and generate correct symlink inside the folder

    """

    def __init__(self, buildout, name, options):
        """Initialize properties

        :ivar auto_run_dir: path to auto-run folder
        :ivar auto_run_script: path to generated autorun.sh
        :ivar template_path: path to the template use to
                             generate autorun.sh
        :ivar supervisor_command_path: path to supervisorctl
        :ivar supervisor_daemon_path: path to supervisord
        :ivar start_on_boot: if True script will generate symlink
        :ivar log: logger

        """

        self.auto_run_dir = os.path.join(
            buildout['buildout']['directory'],
            AUTORUNDIR
        )
        self.auto_run_script_path = os.path.join(
            buildout['buildout']['directory'],
            BINPATH,
            AUTORUNSCRIPT
        )
        self.template_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            TEMPLATENAME
        )
        self.supervisor_daemon_path = os.path.join(
            buildout['buildout']['directory'],
            BINPATH,
            SUPERVISORDAEMON,
        )
        self.supervisor_pid = buildout['supervisor']['pidfile']
        self.current_instance = buildout['erp_global']['current_instance']

        self.name, self.options = name, options
        self.log = logging.getLogger(self.name)
        self.start_on_boot = self.getboolean(
            options.get('start_on_boot', False)
        )

    def getboolean(self, val):
        """Parse boolean set in buildout file

        :param val: string read from config file

        :returns: corresponding boolean

        """
        ok = ['1', 'True', 'yes', 'ok', 'on']
        ko = ['0', 'False', 'no', 'ko', 'off']
        if str(val).lower() in ok:
            return True
        elif str(val).lower() in ko:
            return False
        else:
            raise ValueError('Invalid value for bool, must be in %s' % ok + ko)

    def manage_autorun_dir(self):
        """Create or recreate auto-run folder"""
        if os.path.exists(self.auto_run_dir):
            if os.path.isdir(self.auto_run_dir):
                shutil.rmtree(self.auto_run_dir)
            else:
                msg = ("%s auto-run is not a directory "
                       "and can not be removed") % self.auto_run_dir
                self.log.error(msg)
                raise zc.buildout.UserError(msg)
        try:
            os.mkdir(self.auto_run_dir)
        except IOError as exc:
            msg = "Unable to create % folder: %s" % (self.auto_run_dir, repr(exc))
            self.log.error(msg)
            raise

    def manage_symlink(self):
        """Generate symlink to autorun.sh if needed"""
        if self.start_on_boot:
            source = self.auto_run_script_path
            dest = os.path.join(self.auto_run_dir, AUTORUNSCRIPT)
            os.symlink(source, dest)

    def generate_auto_run_script(self):
        """Generate autorun.sh file from template file.
        Update it content and ensure permission

        """
        with open(self.template_path) as tpl:
            script_tpl = Template(tpl.read())
        script = script_tpl.substitute(
            supervisor_daemon_path=self.supervisor_daemon_path,
            supervisor_pid=self.supervisor_pid,
            current_instance=self.current_instance
        )
        with open(self.auto_run_script_path, 'w') as script_file:
            script_file.seek(0)
            script_file.write(script)
            script_file.truncate()
            mode = os.stat(self.auto_run_script_path)
            # Add execute permission
            os.chmod(self.auto_run_script_path,
                     mode.st_mode | stat.S_IEXEC)

    def install(self):
        self.generate_auto_run_script()
        self.manage_autorun_dir()
        self.manage_symlink()
        return []

    def update(self):
        self.generate_auto_run_script()
        self.manage_autorun_dir()
        self.manage_symlink()
        return []
