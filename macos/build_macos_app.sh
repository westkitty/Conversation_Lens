#!/bin/zsh
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
MACOS_DIR="$REPO_ROOT/macos"
APP_BUNDLE="$HOME/Applications/Conversation Lens.app"
CONTENTS_DIR="$APP_BUNDLE/Contents"
MACOS_BIN_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
DRIVE_ASSET="/Volumes/wc2tb/stationary/assets/brand/source/west-cat-logo-original.png"
ICON_PNG="$MACOS_DIR/ConversationLensIcon.png"

mkdir -p "$MACOS_BIN_DIR" "$RESOURCES_DIR"

if [ -f "$DRIVE_ASSET" ] || [ ! -f "$ICON_PNG" ]; then
  swift "$MACOS_DIR/generate_icon.swift" "$DRIVE_ASSET" "$ICON_PNG"
fi

TMP_ICON_DIR="$(mktemp -d "${TMPDIR:-/tmp}/lens-iconset.XXXXXX")"
ICONSET_DIR="$TMP_ICON_DIR/AppIcon.iconset"
mkdir -p "$ICONSET_DIR"
trap 'rm -rf "$TMP_ICON_DIR"' EXIT

for sz in 16 32 128 256 512; do
  sips -z "$sz" "$sz" "$ICON_PNG" --out "$ICONSET_DIR/icon_${sz}x${sz}.png" >/dev/null
  sz2=$((sz * 2))
  sips -z "$sz2" "$sz2" "$ICON_PNG" --out "$ICONSET_DIR/icon_${sz}x${sz}@2x.png" >/dev/null
done

iconutil -c icns "$ICONSET_DIR" -o "$RESOURCES_DIR/AppIcon.icns"

cat > "$CONTENTS_DIR/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>en</string>
  <key>CFBundleDisplayName</key>
  <string>Conversation Lens</string>
  <key>CFBundleExecutable</key>
  <string>ConversationLensWrapper</string>
  <key>CFBundleIconFile</key>
  <string>AppIcon</string>
  <key>CFBundleIdentifier</key>
  <string>com.stinkyweasel.conversation-lens</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>Conversation Lens</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>6.0.0</string>
  <key>CFBundleVersion</key>
  <string>6</string>
  <key>LSMinimumSystemVersion</key>
  <string>13.0</string>
  <key>NSHighResolutionCapable</key>
  <true/>
  <key>NSMicrophoneUsageDescription</key>
  <string>Conversation Lens uses your microphone for local, consent-gated speech transcription and tentative speaker identification on this MacBook.</string>
  <key>NSAppTransportSecurity</key>
  <dict>
    <key>NSAllowsLocalNetworking</key>
    <true/>
  </dict>
  <key>NSPrincipalClass</key>
  <string>NSApplication</string>
</dict>
</plist>
PLIST

ENTITLEMENTS_PLIST="$TMP_ICON_DIR/entitlements.plist"
cat > "$ENTITLEMENTS_PLIST" <<'ENT'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>com.apple.security.device.audio-input</key>
  <true/>
  <key>com.apple.security.network.client</key>
  <true/>
  <key>com.apple.security.network.server</key>
  <true/>
</dict>
</plist>
ENT

swiftc -O -parse-as-library \
  "$MACOS_DIR/ConversationLensWrapper.swift" \
  -o "$MACOS_BIN_DIR/ConversationLensWrapper" \
  -framework AppKit \
  -framework WebKit

codesign --force --deep --sign - --entitlements "$ENTITLEMENTS_PLIST" "$APP_BUNDLE"
touch "$APP_BUNDLE"

LSREGISTER="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
if [ -x "$LSREGISTER" ]; then
  "$LSREGISTER" -f "$APP_BUNDLE" || true
fi

if [ "${1:-}" = "--install-dock" ]; then
  /usr/bin/python3 - "$APP_BUNDLE" <<'PY'
import os, plistlib, subprocess, sys, urllib.parse

app_path = os.path.abspath(sys.argv[1])
if not app_path.endswith("/"):
    app_url = "file://" + urllib.parse.quote(app_path) + "/"
else:
    app_url = "file://" + urllib.parse.quote(app_path)

raw = subprocess.check_output(["defaults", "export", "com.apple.dock", "-"])
dock = plistlib.loads(raw)
apps = dock.get("persistent-apps", [])

already = False
for item in apps:
    td = item.get("tile-data", {})
    url = td.get("file-data", {}).get("_CFURLString", "")
    if td.get("file-label") == "Conversation Lens" or url.rstrip("/") == app_url.rstrip("/"):
        td["file-label"] = "Conversation Lens"
        td["file-data"] = {"_CFURLString": app_url, "_CFURLStringType": 15}
        already = True

if not already:
    apps.append({
        "tile-type": "file-tile",
        "tile-data": {
            "file-label": "Conversation Lens",
            "file-data": {
                "_CFURLString": app_url,
                "_CFURLStringType": 15,
            },
        },
    })
    dock["persistent-apps"] = apps

out = plistlib.dumps(dock, fmt=plistlib.FMT_BINARY)
proc = subprocess.Popen(["defaults", "import", "com.apple.dock", "-"], stdin=subprocess.PIPE)
proc.communicate(out)
if proc.returncode != 0:
    raise SystemExit(proc.returncode)
subprocess.run(["killall", "Dock"], check=False)
print("Pinned Conversation Lens.app to macOS Dock:", app_url)
PY
fi

echo "Built native macOS wrapper at: $APP_BUNDLE"
