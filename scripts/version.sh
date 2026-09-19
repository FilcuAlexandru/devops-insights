#!/bin/sh
# Keep the project version consistent.
#
#   scripts/version.sh set 1.2.0     write 1.2.0 into every file that carries the version
#   scripts/version.sh check         fail if those files disagree
#   scripts/version.sh check 1.2.0   fail unless they all say 1.2.0 (used by the release workflow)
#   scripts/version.sh get           print the version
#
# The backend package version is the source of truth. The Helm chart version, chart appVersion,
# image tags and the Makefile follow it.
set -eu

cd "$(dirname "$0")/.."

INIT=backend/src/devops_insights/__init__.py
CHART=deploy/helm/devops-insights/Chart.yaml
VALUES_KIND=deploy/helm/devops-insights/values-kind.yaml
VALUES_OPENSHIFT=deploy/helm/devops-insights/values-openshift.yaml
BUILD=deploy/openshift/build.yaml
MAKEFILE=Makefile

current() { sed -n 's/^__version__ = "\(.*\)"/\1/p' "$INIT"; }

# Every place that must carry the version, printed as "file: value".
report() {
    echo "$INIT: $(current)"
    echo "$CHART (version): $(sed -n 's/^version: //p' "$CHART")"
    echo "$CHART (appVersion): $(sed -n 's/^appVersion: "\(.*\)"/\1/p' "$CHART")"
    echo "$VALUES_KIND (tags): $(sed -n 's/^ *tag: "\(.*\)"/\1/p' "$VALUES_KIND" | sort -u | tr '\n' ' ')"
    echo "$VALUES_OPENSHIFT (tags): $(sed -n 's/^ *tag: "\(.*\)"/\1/p' "$VALUES_OPENSHIFT" | sort -u | tr '\n' ' ')"
    echo "$BUILD (tags): $(sed -n 's/^ *name: devops-insights-[a-z]*:\(.*\)/\1/p' "$BUILD" | sort -u | tr '\n' ' ')"
    echo "$MAKEFILE (IMAGE_TAG): $(sed -n 's/^IMAGE_TAG *:= *//p' "$MAKEFILE")"
}

case "${1:-}" in
    get)
        current
        ;;
    set)
        version="${2:?usage: $0 set X.Y.Z}"
        echo "$version" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' || { echo "Not a semantic version: $version" >&2; exit 2; }
        sed -i.bak "s/^__version__ = .*/__version__ = \"$version\"/" "$INIT"
        sed -i.bak "s/^version: .*/version: $version/; s/^appVersion: .*/appVersion: \"$version\"/" "$CHART"
        sed -i.bak "s/^\( *tag: \)\"[^\"]*\"/\1\"$version\"/" "$VALUES_KIND" "$VALUES_OPENSHIFT"
        sed -i.bak "s/\(name: devops-insights-[a-z]*\):.*/\1:$version/" "$BUILD"
        sed -i.bak "s/^IMAGE_TAG *:=.*/IMAGE_TAG      := $version/" "$MAKEFILE"
        find . -name '*.bak' -not -path './.git/*' -delete
        echo "Version set to $version. Review with: git diff"
        ;;
    check)
        expected="${2:-$(current)}"
        report | while IFS= read -r line; do
            value="${line#*: }"
            # A field may hold several space-separated values; every one must match.
            for item in $value; do
                [ "$item" = "$expected" ] || { echo "Version mismatch, expected $expected: $line" >&2; exit 1; }
            done
        done
        echo "All version fields are $expected."
        ;;
    *)
        echo "usage: $0 get | set X.Y.Z | check [X.Y.Z]" >&2
        exit 2
        ;;
esac
