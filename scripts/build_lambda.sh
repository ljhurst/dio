#!/usr/bin/env bash
# Builds dist/dio.zip: third-party dependencies for Lambda's linux/x86_64
# runtime (resolved by uv, no Docker needed) plus the dio package.
#
# Reproducible: every file's mtime is normalized, entries are added in sorted
# order and -X strips extra fields, so an unchanged tree gives an identical
# zip. Without that, source_code_hash changes on every build and Terraform
# reports code drift.
set -euo pipefail

cd "$(dirname "$0")/.."

rm -rf build dist
mkdir -p build/package dist

uv export -q --frozen --no-dev --no-emit-project --no-editable \
  --format requirements-txt -o build/requirements.txt

uv pip install -q \
  --no-installer-metadata \
  --no-compile-bytecode \
  --python-platform x86_64-manylinux2014 \
  --python 3.13 \
  --target build/package \
  -r build/requirements.txt

rsync -a --exclude='*.pyc' --exclude='__pycache__' src/dio build/package/

find build -exec touch -t 202001010000.00 {} +

(cd build/package && find . -type f | LC_ALL=C sort | zip -Xq@ "../../dist/dio.zip")

rm -rf build

echo "Built $(pwd)/dist/dio.zip"
