#!/usr/bin/env bash
buildozer android debug deploy run &
pid=$!

pass=$(zenity --entry)
wait $pid || let "FAIL=1"

if [ $FAIL ]; then
  echo "Build Failed."
else
  echo unlocking screen...
  adb shell input text $pass
  adb shell input keyevent 66
  adb logcat | grep python
fi
