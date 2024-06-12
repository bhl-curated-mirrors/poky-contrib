#! /bin/sh


THIS_DIR="$(dirname "$0")"


shacl2code generate --input https://spdx.org/rdf/3.0.0/spdx-model.ttl \
    --input https://spdx.org/rdf/3.0.0/spdx-json-serialize-annotations.ttl \
    --context https://spdx.org/rdf/3.0.0/spdx-context.jsonld \
    python -o $THIS_DIR/../../meta/lib/oe/spdx30.py

