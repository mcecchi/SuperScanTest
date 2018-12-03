import sys
import os
import getopt
import subprocess
import time
import threading
import json
from kivy.event import EventDispatcher
from kivy.clock import Clock
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from shell import Shell

PYTHON_EXECUTABLE = "python"
SCANNER_SCRIPT_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "scanner")
PY_SCANNER_LIMIT_SWITCH_SCRIPT = os.path.join(
    SCANNER_SCRIPT_DIR, "scanner_limit_switch.py")
PY_SCANNER_BASE_SCRIPT = os.path.join(
    SCANNER_SCRIPT_DIR, "scanner_base.py")
PY_SWEEP_TEST_SCRIPT = os.path.join(
    SCANNER_SCRIPT_DIR, "sweep_test.py")
PY_CLEANUP_SCRIPT = os.path.join(
    SCANNER_SCRIPT_DIR, "cleanup.py")
PY_SCAN_SCRIPT = os.path.join(
    SCANNER_SCRIPT_DIR, "scanner.py")
SCAN_FILE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "../output_scans/")


class TestRoot(BoxLayout):
    def __init__(self, use_dummy=False, filename=None, **kwargs):
        super(TestRoot, self).__init__(**kwargs)
        self.use_dummy = use_dummy
        self.filename = filename
        self.resetting = False
        self.shell = Shell()
        self.shell.bind(on_stdout=self.on_stdout)
        self.shell.bind(on_stderr=self.on_stderr)
        self.shell.bind(on_exit=self.on_exit)
        self.ids.quit.bind(on_press=lambda x: self.stop())
        self.ids.scan.bind(state=self.on_state_scan)

    def on_state_scan(self, instance, value):
        if self.resetting is True:
            self.resetting = False
        else:
            if value == 'down':
                print 'START SCAN'
                self.execute()
            else:
                print 'CANCEL SCAN'
                self.shutdown()

    def execute(self):
        self.ids.pb.value = 0
        # note the -u here: essential for not buffering
        # the stdout of the subprocess
        args = [PYTHON_EXECUTABLE,
                '-u',
                PY_SCAN_SCRIPT,
                '--motor_speed=1',
                '--sample_rate=500',
                '--angular_range=180',
                '--min_range_val=10',
                '--max_range_val=4000']
        if self.filename is not None:
            args.append('--output={}'.format(self.filename))
        if self.use_dummy:
            args.append('--use_dummy')
        self.shell.run(args)

    def on_exit(self, instance, returncode):
        print('Child process quit with code : {}\n'.format(returncode))
        self.reset_toggle()

    def on_stdout(self, instance, line):
        data = json.loads(line)
        if data['status'] == 'failed':
            self.safe_shutdown()
        elif data['status'] == 'scan':
            self.ids.pb.value = \
                round(100 * ((data['duration'] -
                              data['remaining']) / data['duration']))

    def on_stderr(self, instance, line):
        print('STDERR: {}'.format(line))
        self.safe_shutdown()

    def reset_toggle(self):
        if self.ids.scan.state == 'down':
            self.resetting = True
            self.ids.scan.state = 'normal'

    def safe_shutdown(self):
        Clock.schedule_once(lambda dt: self.shutdown(), 0.5)

    def shutdown(self):
        self.shell.stop()
        # cleanupAfterUnexpectedShutdown();
        self.reset_toggle()

    def stop(self):
        self.shutdown()
        App.get_running_app().stop()


class TestApp(App):
    def __init__(self, use_dummy=False, filename=None, **kwargs):
        super(TestApp, self).__init__(**kwargs)
        self.use_dummy = use_dummy
        self.filename = filename

    def build(self):
        return TestRoot(use_dummy=self.use_dummy, filename=self.filename)


if __name__ == '__main__':
    try:
        opts, _ = getopt.getopt(sys.argv[1:], 'do:', ['use_dummy', 'output='])
    except getopt.GetoptError:
        print('Usage: python {} [-- [[-d]|[--use_dummy]]'
              '[[-o <file>]|[--output=<file>]]]'.format(sys.argv[0]))
        sys.exit()
    use_dummy = False
    filename = None
    for o, a in opts:
        if o in ("-d", "--use_dummy"):
            use_dummy = True
        elif o in ("-o", "--output"):
            filename = a
    TestApp(use_dummy=use_dummy, filename=filename).run()
