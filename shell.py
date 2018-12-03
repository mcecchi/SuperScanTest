import subprocess
import threading
from kivy.event import EventDispatcher


class Shell(EventDispatcher):
    def __init__(self, **kwargs):
        self.register_event_type('on_stdout')
        self.register_event_type('on_stderr')
        self.register_event_type('on_exit')
        super(Shell, self).__init__(**kwargs)
        self.proc = None

    def on_stdout(self, line):
        print('STDOUT: {}'.format(line))

    def on_stderr(self, line):
        print('STDERR: {}'.format(line))

    def on_exit(self, returncode):
        print('Child process quit with code : {}\n'
              .format(self.proc.returncode))

    def run(self, command):
        self.proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        threading.Thread(target=self.output_reader, args=(self.proc,)).start()
        threading.Thread(target=self.error_reader, args=(self.proc,)).start()

    def output_reader(self, proc):
        for line in iter(proc.stdout.readline, b''):
            self.dispatch('on_stdout', line)
        self.proc.wait()
        self.dispatch('on_exit', self.proc.returncode)

    def error_reader(self, proc):
        for line in iter(proc.stderr.readline, b''):
            self.dispatch('on_stderr', line)

    def stop(self):
        if self.proc is not None:
            self.proc.kill()
