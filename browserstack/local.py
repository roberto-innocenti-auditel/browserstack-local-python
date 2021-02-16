import subprocess, os, json, psutil
from typing import List
from browserstack.local_binary import LocalBinary
from browserstack.bserrors import BrowserStackLocalError
import re, time
import logging

logger = logging.getLogger(__name__)

class Local:
    def __init__(self, key=None, binary_path=None, **kwargs):
        self.key = os.environ.get('BROWSERSTACK_ACCESS_KEY', key)
        self.binary_path = binary_path or LocalBinary().get_binary()
        self.proc = None
        self.pid = None
        self.options = kwargs
        if 'log-file' not in self.options:
            self.options['log-file'] = os.path.join(os.getcwd(), 'local.log')
        
    def __encode_cmdline_arg(self, key, value) -> List[str]:
        if key is None or value is None:
            return ['']
        prefix = '--'
        if len(key) == 1:
            prefix = '-'
        if str(value).lower() == "true":
            return [prefix + key]
        else:
            return [prefix + key, str(value)]

    def _generate_cmd(self) -> List[str]:
        cmd = [self.binary_path, '--daemon', 'start', "--key", self.key]
        for o in self.options.keys():
            cmd = cmd + self.__encode_cmdline_arg(o, self.options[o])
        return cmd

    def _generate_stop_cmd(self) -> List[str]:
        cmd = self._generate_cmd()
        cmd[2] = 'stop'
        return cmd

    def __kwargs_to_options(self, kwargs):
        """ camelCase -> camel-case"""

        return {
            re.sub(r"([A-Z])", lambda m: "-" + m.group(1).lower(), arg):argvalue \
                for arg, argvalue in kwargs.items()
        }
    
    def start(self, options:dict=None, **kwargs):
        options = options or {}
        if kwargs:
            options.update(self.__kwargs_to_options(kwargs))
        if 'key' in options:
            self.key = options.pop('key')
        if 'binarypath' in options:
            self.binary_path = options.pop('binarypath')
        self.options.update(options)

        if "only-command" in options and options["only-command"]:
            return

        bs_command = self._generate_cmd()
        logger.debug("Starting browserstack local with command: %s" % bs_command)
        self.proc = subprocess.Popen(bs_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.debug("Waiting for process to start..")
        (out, err) = self.proc.communicate()
        out, err = out.decode(), err.decode()
        if err:
            try:
                data = json.loads(err)
                raise BrowserStackLocalError(data["message"]["message"])
            except json.decoder.JSONDecodeError:
                logger.error("Command line error: %s" % err, exc_info=True)
                raise BrowserStackLocalError(err)
        try:
            data = json.loads(out)
            if data['state'] != "connected":
                raise BrowserStackLocalError(data["message"]["message"])
            else:
                self.pid = data['pid']
            logger.debug("Started pid: %d" % self.pid)
        except ValueError:
            raise BrowserStackLocalError('Error parsing JSON output from daemon')

    def isRunning(self) -> bool:        
        return self.pid is not None and psutil.pid_exists(self.pid)

    def _kill_all(self, timeout=20):
        p = psutil.Process(self.pid)
        for child in p.children(recursive=True):
            child.kill()
        p.kill()
        p.wait(timeout=timeout)
    
    def stop(self) -> bool:
        result = False
        try:
            bs_command = self._generate_stop_cmd()
            logger.debug("Stopping browserstack local with command: %s" % bs_command)
            proc = subprocess.Popen(bs_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.debug("Waiting process to terminate..")
            (out, err) = proc.communicate()
            out, err = out.decode(), err.decode()
            if err:
                logger.warning("Stop command error: %s" % err)
            if self.pid and psutil.pid_exists(self.pid):
                logger.warning("Process still alive after stop. Killing process %s.." % self.pid)
                try:
                    self._kill_all()
                    result = psutil.pid_exists(self.pid) is False
                except psutil.TimeoutExpired:
                    logger.warn("Unable to kill pid %s" % self.pid)
            else:
                result = True
        except Exception as e:
            logger.error("Stop command raised exception: %s" % e, exc_info=True)
        return result

    def __enter__(self):
        self.start(**self.options)
        return self

    def __exit__(self, *args):
        self.stop()

