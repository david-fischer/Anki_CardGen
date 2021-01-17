SRC_DIR=$1
SPEC_FILE=${2:-*.spec}
OUT_PATH=$3

cd "$SRC_DIR" || exit
pyinstaller --clean -y --distpath "$OUT_PATH" "$SPEC_FILE"
chown -R --reference=. "$OUT_PATH"
