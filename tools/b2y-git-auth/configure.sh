#!/usr/bin/env bash
# Configure only the user's private B2Y repository; never embed a token here.
set +x
set -euo pipefail
umask 077
repo=/home/y00937463/B2Y
credential_dir=/home/y00937463/.config/git-b2y
credential_file=$credential_dir/credentials
username=JotaroSSR

test "$(git -C "$repo" branch --show-current)" != '' || { echo 'ERROR: repository unavailable'; exit 1; }
case "$(git -C "$repo" remote get-url origin)" in
  https://gitcode.com/JotaroSSR/B2Y.git|https://gitcode.com/JotaroSSR/B2Y) ;;
  *) echo 'ERROR: unexpected origin; no configuration changed'; exit 1 ;;
esac
test ! -L "$credential_dir" && test ! -L "$credential_file" || { echo 'ERROR: credential path is a symlink'; exit 1; }
printf 'GitCode token (hidden input): ' > /dev/tty
IFS= read -r -s b2y_token < /dev/tty
printf '\n' > /dev/tty
test -n "$b2y_token" || { echo 'ERROR: empty token; no configuration changed'; exit 1; }
trap 'unset b2y_token' EXIT
resolved_credential_dir=$(realpath -m "$credential_dir")
case "$resolved_credential_dir" in
  /home/y00937463/*) ;;
  *) echo 'ERROR: credential directory resolves outside the private root'; exit 1 ;;
esac
mkdir -p "$credential_dir"
chmod 700 "$credential_dir"
touch "$credential_file"
chmod 600 "$credential_file"
# Empty local helper overrides inherited helpers for this repository only.
git -C "$repo" config --local --replace-all credential.helper ''
git -C "$repo" config --local --add credential.helper "store --file=$credential_file"
git -C "$repo" config --local credential.useHttpPath true
git -C "$repo" config --local credential.https://gitcode.com.username "$username"
git -C "$repo" config --local user.name "$username"
git -C "$repo" config --local user.email '1224862686@qq.com'
printf 'protocol=https\nhost=gitcode.com\npath=JotaroSSR/B2Y.git\nusername=%s\npassword=%s\n\n' "$username" "$b2y_token" |
  git -C "$repo" credential approve
unset b2y_token
chmod 600 "$credential_file"
echo 'CONFIGURED: repository-local persistent credential store (plaintext, mode 600).'
echo 'Token was not printed or committed. Authentication is checked on the next push.'
echo 'This does not change proxy, TLS verification, global Git configuration, or merge state.'
