# coding=utf-8
from datetime import datetime
from sys import argv

with open(argv[1], 'r+') as f:
  content = f.read()
  f.seek(0)
  f.write(content.replace('VERSION-PLACEHOLDER', datetime.now().isoformat()))
