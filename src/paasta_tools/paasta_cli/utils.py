import fnmatch
import glob
import os
import shlex
from socket import create_connection
from socket import error
from socket import gaierror
from socket import gethostbyname_ex
from subprocess import PIPE
from subprocess import Popen
from subprocess import STDOUT

from service_configuration_lib import read_services_configuration


def load_method(module_name, method_name):
    """Return a function given a module and method name.

    :param module_name: a string
    :param method_name: a string
    :return: a function
    """
    module = __import__(module_name, fromlist=[method_name])
    method = getattr(module, method_name)
    return method


def file_names_in_dir(directory):
    """Read and return the files names in the directory.

    :return: a list of strings such as ['list','check'] that correspond to the
    files in the directory without their extensions."""
    dir_path = os.path.dirname(os.path.abspath(directory.__file__))
    path = os.path.join(dir_path, '*.py')

    for file_name in glob.glob(path):
        basename = os.path.basename(file_name)
        root, _ = os.path.splitext(basename)
        if root == '__init__':
            continue
        yield root


def is_file_in_dir(file_name, path):
    """Recursively search path for file_name.

    :param file_name: a string of a file name to find
    :param path: a string path
    :param file_ext: a string of a file extension
    :return: a boolean"""
    for root, dirnames, filenames in os.walk(path):
        for filename in filenames:
            if fnmatch.fnmatch(filename, file_name):
                return os.path.join(root, filename)
    return False


def check_mark():
    """
    :return: string that can print a checkmark"""
    return PaastaColors.green(u'\u2713'.encode('utf-8'))


def x_mark():
    """
    :return: string that can print an x-mark"""
    return PaastaColors.red(u'\u2717'.encode('utf-8'))


def success(msg):
    """Format a paasta check success message.

    :param msg: a string
    :return: a beautiful string"""
    return "%s %s" % (check_mark(), msg)


def failure(msg, link):
    """Format a paasta check failure message.

    :param msg: a string
    :return: a beautiful string"""
    return "%s %s %s" % (x_mark(), msg, PaastaColors.blue(link))


class PaastaColors:
    """Collection of static variables and methods to assist in coloring text."""
    # ANSI colour codes
    DEFAULT = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    YELLOW = '\033[33m'

    @staticmethod
    def bold(text):
        """Return bolded text.

        :param text: a string
        :return: text colour coded with ANSI bold
        """
        return PaastaColors.color_text(PaastaColors.BOLD, text)

    @staticmethod
    def blue(text):
        """Return text that can be printed cyan.

        :param text: a string
        :return: text colour coded with ANSI blue
        """
        return PaastaColors.color_text(PaastaColors.BLUE, text)

    @staticmethod
    def green(text):
        """Return text that can be printed cyan.

        :param text: a string
        :return: text colour coded with ANSI green"""
        return PaastaColors.color_text(PaastaColors.GREEN, text)

    @staticmethod
    def red(text):
        """Return text that can be printed cyan.

        :param text: a string
        :return: text colour coded with ANSI red"""
        return PaastaColors.color_text(PaastaColors.RED, text)

    @staticmethod
    def color_text(color, text):
        """Return text that can be printed color.

        :param color: ANSI colour code
        :param text: a string
        :return: a string with ANSI colour encoding"""
        return color + text + PaastaColors.DEFAULT

    @staticmethod
    def cyan(text):
        """Return text that can be printed cyan.

        :param text: a string
        :return: text colour coded with ANSI cyan"""
        return PaastaColors.color_text(PaastaColors.CYAN, text)

    @staticmethod
    def yellow(text):
        """Return text that can be printed yellow.

        :param text: a string
        :return: text colour coded with ANSI yellow"""
        return PaastaColors.color_text(PaastaColors.YELLOW, text)


class PaastaCheckMessages:
    """Collection of message printed out by 'paasta check'.
    Helpful as it avoids cumbersome maintenance of the unit tests."""

    DEPLOY_YAML_FOUND = success("deploy.yaml exists for a Jenkins pipeline")

    DEPLOY_YAML_MISSING = failure(
        "No deploy.yaml exists, so your service cannot be deployed.\n  "
        "Push a deploy.yaml and run `paasta build-deploy-pipline`.\n  "
        "More info:", "http://y/yelpsoa-configs")

    DOCKERFILE_FOUND = success("Found Dockerfile")

    DOCKERFILE_MISSING = failure(
        "Dockerfile not found. Create a Dockerfile and try again.\n  "
        "More info:", "http://y/paasta-runbook-dockerfile")

    DOCKERFILE_EXPOSES_8888 = success("Found 'EXPOSE 8888' in Dockerfile")

    DOCKERFILE_DOESNT_EXPOSE_8888 = failure(
        "Couldn't find 'EXPOSE 8888' in Dockerfile. Your service must respond\n"
        "  to 8888. The Dockerfile should expose that per the doc linked "
        "below.\n  More info:", "http://y/paasta-contract")

    DOCKERFILE_YELPCORP = success(
        "Your Dockerfile pulls from the standard Yelp images.")

    DOCKERFILE_NOT_YELPCORP = failure(
        "Your Dockerfile does not use the standard Yelp images.\n  "
        "This is bad because your `docker pulls` will be slow and you won't be "
        "using the local mirrors.\n  "
        "More info:", "http://y/paasta-runbook-dockerfile")

    GIT_REPO_FOUND = success("Git repo found in the expected location.")

    MARATHON_YAML_FOUND = success("Found marathon.yaml file.")

    MARATHON_YAML_MISSING = failure(
        "No marathon.yaml exists, so your service cannot be deployed.\n  "
        "Push a marathon-[ecosystem].yaml and run `paasta build-deploy-pipline`.\n  "
        "More info:", "http://y/yelpsoa-configs")

    MAKEFILE_FOUND = success("A Makefile is present")
    MAKEFILE_MISSING = failure(
            "No Makefile available. Please make a Makefile that responds\n"
            "to the proper targets. More info:", "http://y/paasta-contract")
    MAKEFILE_RESPONDS_ITEST = success("The Makefile responds to `make itest`")
    MAKEFILE_RESPONDS_ITEST_FAIL = failure(
            "The Makefile does not have a `make itest` target. Jenkins needs\n"
            "this and expects it to build and itest your docker image. More info:",
            "http://y/paasta-contract")

    PIPELINE_FOUND = success("Jenkins build pipeline found")

    PIPELINE_MISSING = failure("Jenkins build pipeline missing. Please run "
                               "'paasta generate-pipeline'\n"
                               "  More info:", "http://y/paasta-deploy")

    SENSU_MONITORING_FOUND = success(
        "monitoring.yaml found for Sensu monitoring")

    SENSU_MONITORING_MISSING = failure(
        "Your service is not using Sensu (monitoring.yaml).\n  "
        "Please setup a monitoring.yaml so we know where to send alerts.\n  "
        "More info:", "http://y/monitoring-yaml")

    SENSU_TEAM_MISSING = failure(
        "Cannot get team name. Ensure 'team' field is set in monitoring.yaml.\n"
        "  More info:", "http://y/monitoring-yaml")

    SMARTSTACK_YAML_FOUND = success("Found smartstack.yaml file")

    SMARTSTACK_YAML_MISSING = failure(
        "Your service is not setup on smartstack yet and will not be "
        "automatically load balanced.\n  "
        "More info:", "http://y/smartstack-cep323")

    SMARTSTACK_PORT_MISSING = failure(
        "Could not determine port. "
        "Ensure 'proxy_port' is set in smartstack.yaml.\n  "
        "More info:", "http://y/smartstack-cep323")

    @staticmethod
    def git_repo_missing(service_name):
        git_url = PaastaColors.cyan(
            "http://git.yelpcorp.com:services/%s" % service_name)
        return failure(
            "Could not find Git repo %s. "
            "Your service must be there.\n"
            "  More info:" % git_url,
            "http://y/yelpsoa-configs")

    @staticmethod
    def sensu_team_found(team_name):
        return success(
            "Your service uses Sensu and team %s will get alerts." % team_name)

    @staticmethod
    def smartstack_port_found(instance, port):
        return success(
            "Instance '%s' of your service is using smartstack port %d "
            "and will be automatically load balanced" % (instance, port))

    @staticmethod
    def service_dir_found(service_name):
        message = "yelpsoa-config directory for %s found in /nail/etc/services" \
                  % PaastaColors.cyan(service_name)
        return success(message)

    @staticmethod
    def service_dir_missing(service_name):
        message = "Failed to locate yelpsoa-config directory for %s.\n" \
                  "  Please follow the guide linked below to get boilerplate." \
                  % service_name
        return failure(message, "http://y/paasta-deploy")


class NoSuchService(Exception):
    """Exception to be raised in the event that the service
    name can not be guessed."""
    GUESS_ERROR_MSG = "Could not determine service name.\n" \
                      "Please run this from the root of a copy " \
                      "(git clone) of your service.\n" \
                      "Alternatively, supply the %s name you wish to " \
                      "inspect with the %s option." \
                      % (PaastaColors.cyan('SERVICE'), PaastaColors.cyan('-s'))

    CHECK_ERROR_MSG = "not found.  Please provide a valid service name.\n" \
                      "Ensure that a directory of the same name exists in %s."\
                      % PaastaColors.green('/nail/etc/services')

    def __init__(self, service):
        self.service = service

    def __str__(self):
        if self.service:
            return "SERVICE: %s %s" \
                   % (PaastaColors.cyan(self.service), self.CHECK_ERROR_MSG)
        else:
            return self.GUESS_ERROR_MSG


def guess_service_name():
    """Deduce the service name from the pwd
    :return : A string representing the service name
    :raises: NoSuchService exception"""
    return os.path.basename(os.getcwd())


def validate_service_name(service_name):
    """Determine whether directory named service_name exists in
    /nail/etc/services
    :param service_name: a string of the name of the service you wish to check exists
    :return : boolean True
    :raises: NoSuchService exception"""
    service_path = os.path.join('/nail/etc/services', service_name)
    if not os.path.isdir(service_path):
        raise NoSuchService(service_name)


def list_services():
    """Returns a sorted list of all services"""
    return sorted(read_services_configuration().keys())


def calculate_remote_masters(cluster_name):
    cluster_fqdn = "mesos-%s.yelpcorp.com" % cluster_name
    try:
        _, _, ips = gethostbyname_ex(cluster_fqdn)
        output = None
    except gaierror as e:
        output = 'ERROR while doing DNS lookup of %s:\n%s\n ' % (cluster_fqdn, e.strerror)
        ips = []
    return (ips, output)


def find_connectable_master(masters):
    """For each host in the iterable 'masters', try various connectivity
    checks. For each master that fails, emit an error message about which check
    failed and move on to the next master. If a master passes all checks,
    return it as the connectable master. If no masters pass all checks, return
    None.
    """
    port = 22
    timeout = 1.0  # seconds

    connectable_master = None
    for master in masters:
        try:
            create_connection((master, port), timeout)
            # If that succeeded, the connection was successful and we've found
            # our master.
            connectable_master = master
            output = None
            break
        except error as e:
            output = 'ERROR cannot connect to %s port %s:\n%s ' % (master, port, e.strerror)
    return (connectable_master, output)


def _run(command):
    """Given a command, run it. Return a tuple of the return code and any
    output.

    We wanted to use plumbum instead of rolling our own thing with
    subprocess.Popen but were blocked by
    https://github.com/tomerfiliba/plumbum/issues/162 and our local BASH_FUNC
    magic.
    """
    try:
        process = Popen(shlex.split(command), stdout=PIPE, stderr=STDOUT)
        output, _ = process.communicate()    # execute it, the output goes to the stdout
        rc = process.wait()    # when finished, get the exit code
    except OSError as e:
        output = e.strerror
        rc = e.errno
    return (rc, output)


def check_ssh_and_sudo_on_master(master):
    check_command = 'ssh -A -n %s sudo paasta_serviceinit -h' % master
    rc, output = _run(check_command)
    if rc == 0:
        return (True, None)
    if rc == 255:  # ssh error
        reason = 'Return code was %d which probably means an ssh failure.' % rc
        hint = 'HINT: Are you allowed to ssh to this machine %s?' % master
    if rc == 1:  # sudo error
        reason = 'Return code was %d which probably means a sudo failure.' % rc
        hint = 'HINT: Is your ssh agent forwarded? (ssh-add -l)'
    else:  # unknown error
        reason = 'Return code was %d which is an unknown failure.' % rc
        hint = 'HINT: Talk to #operations and pastebin this output'
    output = ('ERROR cannot run check command %(check_command)s\n'
              '%(reason)s\n'
              '%(hint)s\n'
              'Output from check command: %(output)s' %
              {
                  'check_command': check_command,
                  'reason': reason,
                  'hint': hint,
                  'output': output,
              })
    return (False, output)


def run_paasta_serviceinit(subcommand, master, service_name, instancename):
    command = 'ssh -A -n %s sudo paasta_serviceinit %s.%s %s' % (master, service_name, instancename, subcommand)
    _, output = _run(command)
    return output


def execute_paasta_serviceinit_on_remote_master(subcommand, cluster_name, service_name, instancename):
    """Returns a string containing an error message if an error occurred.
    Otherwise returns the return value of run_paasta_serviceinit_status().
    """
    masters, output = calculate_remote_masters(cluster_name)
    if masters == []:
        return 'ERROR: %s' % output
    master, output = find_connectable_master(masters)
    if not master:
        return (
            'ERROR could not find connectable master in cluster %s\nOutput: %s' % (cluster_name, output)
        )
    check, output = check_ssh_and_sudo_on_master(master)
    if not check:
        return 'ERROR ssh or sudo check failed for master %s\nOutput: %s' % (master, output)
    return run_paasta_serviceinit(subcommand, master, service_name, instancename)