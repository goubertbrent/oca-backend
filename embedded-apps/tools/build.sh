project=$1
current_dir="$(
  cd "$(dirname "$0")" >/dev/null 2>&1
  pwd -P
)"

if [ -z "${project}" ]; then
  echo "Select the project that you want to build"
  select project in "oca" "hoplr"; do
    break
  done
fi
npm run ng build -- --prod --project "${project}"
rm -f "${project}".zip
dist_dir=${current_dir}/../dist
cd ${dist_dir}/${project}
zip_path=${current_dir}/../"${project}".zip
zip -qr "$zip_path" .
cd -
