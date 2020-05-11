#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
cd ${DIR}
generateDS -f --no-questions --external-encoding='utf-8' -o gen.py -s sub.py ../../../service/api/MessageFlow.1.xsd
python2 ../../../../../tools/generate_mfd_stubs.py
