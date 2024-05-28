#!/usr/bin/env bash

main() {
  ./generate_proto_for_python.sh
  ./decode_migration_url.py $1
}

main "$@"
