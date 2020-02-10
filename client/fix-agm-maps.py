# coding=utf-8
# temporary fix until angular-google-maps properly supports angular 9
filename = 'node_modules/@agm/core/core.module.d.ts'
with open(filename, 'r+') as f:
  content = f.read().replace('ModuleWithProviders;', 'ModuleWithProviders<AgmCoreModule>;')
  f.seek(0)
  f.write(content)
