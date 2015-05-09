#!/bin/sh

MAJOR_VERSION=`cat src/major-version.txt`
MINOR_VERSION=`cat src/minor-version.txt`
FULL_VERSION="$MAJOR_VERSION-$MINOR_VERSION"
CHANGES_FILE="${MAJOR_VERSION}_${MINOR_VERSION}-1_source.changes"
ORIG_FILE="${MAJOR_VERSION}_${MINOR_VERSION}.orig.tar.xz"

cp -r src $FULL_VERSION

# Substitute the version number
python3 -c "
path = '$FULL_VERSION/debian/changelog'
with open(path) as fh:
  TEXT = fh.read().format(VERSION='$MINOR_VERSION')
with open(path, 'w') as fh:
  fh.write(TEXT)
"

tar cfJ "$ORIG_FILE" $FULL_VERSION

cd $FULL_VERSION
debuild -S -sa -k412C4B95
cd ..
dput ppa:musikernel/musikernel1 $CHANGES_FILE
rm -rf "${MAJOR_VERSION}"{-,_}"${MINOR_VERSION}"*

