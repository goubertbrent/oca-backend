tail -f $1 | perl -pe 's/^INFO/\e[1;32m$&\e[0m/g; s/^WARNING.*$/\n\e[1;33m$&\e[0m\n/g; s/^ERROR.*$/\n\e[1;31m$&\e[0m\n/g; s/^CRITICAL.*$/\n\e[1;31m$&\e[0m\n/g;'
