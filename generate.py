#!/usr/bin/env python

"""Generate themes based on a template"""

import __builtin__

try:
  import ConfigParser
except ImportError: # Python 3
  import configparser as ConfigParser

import argparse
import logging
import os
import re

REGEX = re.compile(r'^.*\$([a-zA-Z]+).*$')

OUTPUT_FILE_NAME = 'Solarized Space %s.sublime-theme'

class Theme(object):
    def __init__(self, data, out):
        self.data = data
        self.out = out

    def add_line(self, line, match):
        rgb = self.data.get(match.lower(), None)
        if rgb is not None:
          if rgb.startswith('"'): # workaround
            raw = rgb
          else:
            raw = [int(x) for x in rgb.split(',')]
          self.out.write(line.replace('$' + match, str(raw)))
        else:
          logging.error('Key "$%s" not found in ini file', match)

def get_files(ini_file):
    parser = ConfigParser.SafeConfigParser()
    parser.read(ini_file)
    themesdata = {}
    sections = parser.sections()
    logging.info('Found %i sections in %s', len(sections), ini_file)
    for section in sections:
      logging.info('Parsing "%s" theme data', section)
      data = dict((k, v) for k, v in parser.items(section))
      if 'basetheme' in data:
        base_theme = data.pop('basetheme')
        if base_theme in themesdata:
          logging.debug('Added "%s" as base theme for "%s"', base_theme, section)
          aux = dict(themesdata[base_theme])
          aux.update(data)
          data = aux
        else:
          logging.error('Base theme "%s" not found', base_theme)
      themesdata[section] = data
      if not section.startswith('.'):
        yield OUTPUT_FILE_NAME % section, data

def generate(ini_file, template):
    themes = [Theme(data, open(name, 'w+')) for name, data in get_files(ini_file)]
    try:
      with open(template, 'r') as istream:
        for line in istream:
          match = REGEX.match(line)
          if match is not None:
            for theme in themes:
              theme.add_line(line, match.group(1))
          else:
            for theme in themes:
              theme.out.write(line)
    finally:
      for theme in themes:
        theme.out.close()

def main():
    argparser = argparse.ArgumentParser(description=__doc__)
    argparser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='print debug information')
    argparser.add_argument(
        '-i', '--ini',
        metavar='INI_FILE',
        dest='ini_file',
        default=os.path.join(os.path.dirname(__file__), 'themes.ini'),
        help='input settings')
    argparser.add_argument(
        '-t', '--template',
        default=os.path.join(os.path.dirname(__file__), 'template.sublime-theme'),
        help='theme template')
    args = argparser.parse_args()

    loglevel = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(format='%(levelname)s: %(message)s', level=loglevel)

    if args.debug:
      try:
        builtin_open = __builtin__.open
        def open_hook(*args, **kwargs):
            logging.debug('Open file: %s', args[0])
            return builtin_open(*args, **kwargs)
        __builtin__.open = open_hook
      except Exception as exception:
        logging.warning('Hook to open failed: %s', exception)

    generate(args.ini_file, args.template)

if __name__ == '__main__':

    main()
