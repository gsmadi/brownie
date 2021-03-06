#!/usr/bin/python3

import sys
import traceback

from lib.services.datatypes import StrictDict
from lib.services import config
CONFIG = config.CONFIG

BASE = "\x1b[0;"

MODIFIERS = {
    'bright':"1;",
    'dark':"2;"
}

COLORS = {
    'black': "30",
    'red': "31",
    'green': "32",
    'yellow': "33",
    'blue': "34",
    'magenta': "35",
    'cyan': "36",
    'white': "37"
}

TB_BASE = (
    "  {0[dull]}File {0[string]}{1[1]}{0[dull]}, line "
    "{0[value]}{1[3]}{0[dull]}, in {0[callable]}{1[5]}{0}{2}"
)


class Color:

    def __call__(self, color = None):
        if color in CONFIG['colors']:
            color = CONFIG['colors'][color]
        if not color:
            return BASE+"m"
        color = color.split()
        try:
            if len(color) == 2:
                return BASE+MODIFIERS[color[0]]+COLORS[color[1]]+"m"
            return BASE+COLORS[color[0]]+"m"
        except KeyError:
            return BASE+"m"

    def __str__(self):
        return BASE+"m"

    def __getitem__(self, color):
        return self(color)

    # format dicts for console printing
    def pretty_dict(self, value, indent = 0, start=True):
        if start:
            sys.stdout.write(' '*indent+'{}{{'.format(self['dull']))
        indent+=4
        for c,k in enumerate(sorted(value, key= lambda k: str(k))):
            if c:
                sys.stdout.write(',')
            sys.stdout.write('\n'+' '*indent)
            if type(k) is str:
                sys.stdout.write("'{0[key]}{1}{0[dull]}': ".format(self, k))
            else:
                sys.stdout.write("{0[key]}{1}{0[dull]}: ".format(self, k))
            if type(value[k]) in (dict, StrictDict):
                sys.stdout.write('{')
                self.pretty_dict(value[k], indent,False)
                continue
            if type(value[k]) in (list, tuple):
                sys.stdout.write(str(value[k])[0])
                self.pretty_list(value[k], indent, False)
                continue
            self._write(value[k])
        indent-=4
        sys.stdout.write('\n'+' '*indent+'}')
        if start:
            sys.stdout.write('\n{}'.format(self))
        sys.stdout.flush()

    # format lists for console printing
    def pretty_list(self, value, indent = 0, start=True):
        brackets = str(value)[0],str(value)[-1]
        if start:
            sys.stdout.write(' '*indent+'{}{}'.format(self['dull'],brackets[0]))
        if value and len(value)==len([i for i in value if type(i) is dict]):
            # list of dicts
            sys.stdout.write('\n'+' '*(indent+4)+'{')
            for c,i in enumerate(value):
                if c:
                    sys.stdout.write(',')
                self.pretty_dict(i, indent+4, False)
            sys.stdout.write('\n'+  ' '*indent+brackets[1])
        elif (
            value and len(value)==len([i for i in value if type(i) is str]) and
            set(len(i) for i in value) == {64}
        ):
            # list of bytes32 hexstrings (stack trace)
            for c,i in enumerate(value):
                if c:
                    sys.stdout.write(',')
                sys.stdout.write('\n'+' '*(indent+4))
                self._write(i)
            sys.stdout.write('\n'+' '*indent+brackets[1])
        else:
            # all other cases
            for c, i in enumerate(value):
                if c:
                    sys.stdout.write(', ')
                self._write(i)
            sys.stdout.write(brackets[1])
        if start:
            sys.stdout.write('\n{}'.format(self))
        sys.stdout.flush()

    def _write(self, value):
        if type(value) is str:
            sys.stdout.write('"{0[string]}{1}{0[dull]}"'.format(self, value))
        else:
            sys.stdout.write('{0[value]}{1}{0[dull]}'.format(self, value))


    # format transaction related console outputs
    def print_colors(self, msg, key = None, value=None):
        if key is None:
            key = 'key'
        if value is None:
            value = 'value'
        for line in msg.split('\n'):
            if ':' not in line:
                print(line)
                continue
            line = line.split(':')
            line[0] = self(key) + line[0]
            line[-1] = self(value) + line[-1]
            for i in range(1,len(line)-1):
                line[i] = (
                    self(value) +
                    line[i][:line[i].index('  ')+1] +
                    self(key) +
                    line[i][line[i].index('  ')+1:]
                )
            line = ":".join(line)
        
            for s in ('(',')','/'):
                line = line.split(s)
                line = s.join([self(value)+i+self(key) for i in line])
            print(line+self())

    def format_tb(self, exc, filename = None, start = None, stop = None):
        tb = [i.replace("./", "") for i in traceback.format_tb(exc[2])]
        if filename and not config.ARGV['tb']:
            try:
                start = tb.index(next(i for i in tb if filename in i))
                stop = tb.index(next(i for i in tb[::-1] if filename in i)) + 1
                tb = tb[start:stop]
            except Exception:
                pass
        for i in range(len(tb)):
            info, code = tb[i].split('\n')[:2]
            info = [x.strip(',') for x in info.strip().split(' ')]
            if 'site-packages/' in info[1]:
                info[1] = '"'+info[1].split('site-packages/')[1]
            tb[i] = TB_BASE.format(self, info, "\n"+code if code else "")
        tb.append("{0[error]}{1}{0}: {2}".format(self, exc[0].__name__, exc[1]))
        return "\n".join(tb)


sys.modules[__name__] = Color()