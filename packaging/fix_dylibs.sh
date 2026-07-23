#!/bin/bash
# Post-build fix for a py2app + cryptography(Rust)/OpenSSL packaging bug.
#
# py2app's dylib-copying step corrupts the Mach-O code signature of
# libssl.3.dylib/libcrypto.3.dylib when rewriting their install names,
# which makes `cryptography`'s Rust extension fail with a dlopen error at
# launch ("load command content extends beyond end of file"). Separately,
# it was found that py2app was going to grab a DIFFERENT (older, symbol-
# incomplete) libssl/libcrypto than the one `cryptography`'s Rust extension
# was actually built against (Homebrew's, from `/usr/local/opt/openssl@3`)
# - using the wrong source produces a "Symbol not found: _EVP_DigestSqueeze"
# error instead. This script copies the CORRECT source libraries in fresh,
# fixes their install names to be app-relative, and re-signs them.
#
# Run this immediately after every `python packaging/setup_py2app.py py2app`.
#
# If this ever stops being necessary (e.g. a py2app/cryptography update
# fixes the underlying bug), the launch error this works around will simply
# disappear and this script becomes safely skippable.

set -euo pipefail

APP="dist/Stardew Valley Save Editor.app"
OPENSSL_LIB="/usr/local/opt/openssl@3/lib"

if [ ! -d "$APP" ]; then
    echo "error: $APP not found - run 'python packaging/setup_py2app.py py2app' first" >&2
    exit 1
fi

if [ ! -f "$OPENSSL_LIB/libssl.3.dylib" ]; then
    echo "error: $OPENSSL_LIB/libssl.3.dylib not found - install Homebrew's openssl@3" >&2
    exit 1
fi

cp "$OPENSSL_LIB/libssl.3.dylib" "$APP/Contents/Frameworks/libssl.3.dylib"
cp "$OPENSSL_LIB/libcrypto.3.dylib" "$APP/Contents/Frameworks/libcrypto.3.dylib"
chmod u+w "$APP/Contents/Frameworks/libssl.3.dylib" "$APP/Contents/Frameworks/libcrypto.3.dylib"

install_name_tool -id "@executable_path/../Frameworks/libssl.3.dylib" \
    "$APP/Contents/Frameworks/libssl.3.dylib"
install_name_tool -id "@executable_path/../Frameworks/libcrypto.3.dylib" \
    "$APP/Contents/Frameworks/libcrypto.3.dylib"

# libssl links to libcrypto via its real (Homebrew Cellar) absolute path -
# resolve that to the actual installed version dynamically and rewrite it
# to the app-relative path so it works on any machine, not just this one.
REAL_CRYPTO_PATH=$(otool -L "$APP/Contents/Frameworks/libssl.3.dylib" | grep libcrypto | awk '{print $1}')
install_name_tool -change "$REAL_CRYPTO_PATH" "@executable_path/../Frameworks/libcrypto.3.dylib" \
    "$APP/Contents/Frameworks/libssl.3.dylib"

codesign --force --sign - "$APP/Contents/Frameworks/libssl.3.dylib"
codesign --force --sign - "$APP/Contents/Frameworks/libcrypto.3.dylib"

echo "Fixed and re-signed libssl.3.dylib / libcrypto.3.dylib in $APP"
