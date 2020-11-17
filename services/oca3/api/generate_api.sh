# Android
androiddir=../../../../mobicage-android-client/rogerthat/src/main/java/com/mobicage/oca
rm -rf $androiddir/infrastructure $androiddir/models
openapi-generator generate -i api.yaml --output $androiddir -c kotlin-config.json -g kotlin
mv $androiddir/src/main/java/com/mobicage/oca/* $androiddir
rm -rf $androiddir/src

# iOS
iosdir=../../../../mobicage-ios-client/src-gen
openapi-generator generate -i api.yaml --output $iosdir -g objc

# Server - module 'default'
openapi-generator generate -i api.yaml --output ../gen -c swagger-config.json -g python-flask

# Server - module 'oca'
openapi-generator generate -i api.yaml --output ../../../src/oca -c swagger-config.json -g python
cd ../../../src/oca
rm -rf api models test docs .gitignore .gitlab-ci.yml .travis.yml git_push.sh README.md requirements.txt setup.cfg setup.py test-requirements.txt tox.ini
mv oca/* .
rmdir oca
cd -

# Web - console
openapi-generator generate -i api.yaml --output ../../../client/projects/console/src/app/communities/homescreen -c swagger-config.json -g typescript-rxjs
rmdir ../../../client/projects/console/src/app/communities/homescreen/apis
