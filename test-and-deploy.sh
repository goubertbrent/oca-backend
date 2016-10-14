set -ex

CUR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

${CUR_DIR}/run_unit_tests.sh
${CUR_DIR}/deploy.sh $1

