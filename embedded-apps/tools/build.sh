project=$1
current_dir="$(
  cd "$(dirname "$0")" >/dev/null 2>&1
  pwd -P
)"

if [ -z "${project}" ]; then
  echo "Select the project that you want to build"
  select project in "oca" "hoplr" "cirklo" "trash-calendar" "participation" "qmatic"; do
    break
  done
fi
set -eu
npm run ng build -- --prod --project "${project}"
rm -f "${project}".zip
dist_dir=${current_dir}/../dist
cd ${dist_dir}/${project}
indexpath="$dist_dir/$project/index.html"
python ../../tools/set-version.py $(realpath "$indexpath")
node ../../tools/remove-unused-svg.js "$dist_dir"/$project
zip_path=${current_dir}/../"${project}".zip
rm -f "$zip_path"
zip -qr "$zip_path" .
cd -
real_zip_path=$(realpath "$zip_path")
echo "Generated embedded app zip: ${real_zip_path}"
