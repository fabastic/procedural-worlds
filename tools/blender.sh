#!/usr/bin/env bash
# Run Blender 5.2 headless from Git Bash. The Store install's blender.exe can't be exec'd directly
# from bash/PowerShell (Access denied); the app-execution alias blender-launcher.exe works and waits,
# but drops stdout. So Python's stdout/stderr are redirected to a log file which is printed after.
#   tools/blender.sh -b --factory-startup -P tools/smoke_test.py -- COASTAL_ISLAND 1
LOG="$(mktemp -t pwblend.XXXXXX).log"
WLOG="$(cygpath -m "$LOG")"
"$LOCALAPPDATA/Microsoft/WindowsApps/blender-launcher.exe" --python-exit-code 3 \
  --python-expr "import sys; sys.stdout = sys.stderr = open('$WLOG', 'w', buffering=1)" "$@"
code=$?
cat "$LOG" 2>/dev/null; rm -f "$LOG"
exit $code
