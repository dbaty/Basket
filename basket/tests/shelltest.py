"""This module defines helper functions to test shell commands
extracted from a reStructuredText file. This is similar to 'doctest',
except that we test the output of shell commands instead of Python
code.

I started from code written by Kumar McMillan for Wikir
(http://code.google.com/p/wikir/ - published under the MIT License)
and then heavily rewrote and simplified it (certainly making it less
generic).
"""

import difflib
import os
import subprocess


PY3 = bytes is not str


def find_shell_sessions(stream):
    cmd = None
    expected_output = []
    block_indent = None
    in_session = False
    line_no = 0
    for line in stream:
        line_no += 1
        if in_session:
            indent = len(line) - len(line.lstrip())
            if indent >= block_indent:
                if line.lstrip()[0] == '$':
                    yield ShellSession(cmd, expected_output, line_no)
                    cmd = line.lstrip(' ')[2:]
                    expected_output = []
                    block_indent = line.find('$')
                else:
                    expected_output.append(line[block_indent:])
            else:
                yield ShellSession(cmd, expected_output, line_no)
                cmd = None
                expected_output = []
                block_indent = None
                in_session = False
        elif not line.startswith(' '):
            continue
        elif line.lstrip()[0] == '$':
            in_session = True
            cmd = line.lstrip(' ')[2:]
            expected_output = []
            block_indent = line.find('$')


class ShellSession(object):

    def __init__(self, cmd, expected_output, line_no):
        self.cmd = cmd
        self.expected_output = expected_output[:]
        self.line_no = line_no

    def __str__(self):
        return unicode(self).encode('utf-8')
    __repr__ = __str__

    def __unicode__(self):
        return '<ShellSession($ %s) at l.%d>' % (self.cmd, self.line_no)

    def replace(self, s, replacement):
        self.cmd = self.cmd.replace(s, replacement)
        for i in range(len(self.expected_output)):
            self.expected_output[i] = self.expected_output[i].replace(
                s, replacement)

    def validate(self):
        saved_wd = os.getcwd()
        try:
            self._validate()
        finally:
            os.chdir(saved_wd)

    def _validate(self):
        if self.cmd.startswith('cd'):
            os.chdir(self.cmd.split(' ')[1].strip())
            return
        p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, close_fds=True,
                             shell=True)
        p.wait()
        output = []
        for stream in (p.stdout, p.stderr):
            while 1:
                line = stream.readline()
                if not line:
                    break
                output.append(line)
        if PY3:
            output = [str(line, 'utf-8') for line in output]
        output = ''.join(output)
        context = os.linesep.join(('Command: %s' % self.cmd.rstrip(),
                                   'Line: %d' % self.line_no,
                                   'Working dir: %s' % os.getcwd()))
        diff = list(difflib.unified_diff(output.splitlines(),
                                         self.expected_output))
        if diff:
            diff = diff[2:]  # remove filenames
        error = os.linesep.join((context, os.linesep.join(diff)))
        assert output == ''.join(self.expected_output), error
