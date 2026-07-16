#!/usr/bin/env sh
set -eu

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

[ -n "${SOURCE_DATABASE_URL:-}" ] || fail "SOURCE_DATABASE_URL is required."
[ -n "${TARGET_DATABASE_URL:-}" ] || fail "TARGET_DATABASE_URL is required."
[ "$SOURCE_DATABASE_URL" != "$TARGET_DATABASE_URL" ] || fail "Source and target database must differ."

parse_test_url() {
  name="$1"
  url="$2"
  case "$url" in
    postgresql://*) ;;
    *) fail "$name must be a postgresql:// URL." ;;
  esac
  case "$url" in *\?*|*\#*|*\|*) fail "$name must not contain query, fragment or pipe characters." ;; esac
  rest="${url#postgresql://}"
  authority="${rest%%/*}"
  database="${rest#*/}"
  host_port="${authority##*@}"
  host="${host_port%%:*}"
  case "$host" in localhost|127.0.0.1|db|postgres) ;; *) fail "$name host is not an allowed local/test host." ;; esac
  echo "$database" | grep -Eq '^[A-Za-z0-9_-]+$' || fail "$name database name contains unsafe characters."
  lower_database="$(printf '%s' "$database" | tr '[:upper:]' '[:lower:]')"
  case "$lower_database" in *test*|*ci*|*synthetic*|*restore*) ;; *) fail "$name database name must clearly identify a test database." ;; esac
  admin_url="${url%/*}/postgres"
  printf '%s|%s\n' "$database" "$admin_url"
}

source_info="$(parse_test_url SOURCE_DATABASE_URL "$SOURCE_DATABASE_URL")"
target_info="$(parse_test_url TARGET_DATABASE_URL "$TARGET_DATABASE_URL")"
SOURCE_DB="${source_info%%|*}"
SOURCE_ADMIN_URL="${source_info#*|}"
TARGET_DB="${target_info%%|*}"
TARGET_ADMIN_URL="${target_info#*|}"

[ "$SOURCE_DB" != "$TARGET_DB" ] || fail "Source and target database names must differ."

for command in pg_dump pg_restore psql createdb dropdb; do
  command -v "$command" >/dev/null 2>&1 || fail "$command is required."
done

work_dir="$(mktemp -d)"
dump_file="$work_dir/program2-synthetic.dump"
trap 'rm -rf "$work_dir"' EXIT

sentinel="PROGRAM2_SYNTHETIC_BACKUP_SENTINEL"
psql "$SOURCE_DATABASE_URL" -v ON_ERROR_STOP=1 -q -c "DELETE FROM patients WHERE notes = '$sentinel'; INSERT INTO patients (first_name,last_name,email,notes) VALUES ('Synthetic','Backup Restore','synthetic.backup@example.invalid','$sentinel');"
source_count="$(psql "$SOURCE_DATABASE_URL" -At -v ON_ERROR_STOP=1 -c "SELECT count(*) FROM patients WHERE notes = '$sentinel'")"
source_checksum="$(psql "$SOURCE_DATABASE_URL" -At -v ON_ERROR_STOP=1 -c "SELECT md5(string_agg(first_name || '|' || last_name || '|' || email || '|' || notes, ',' ORDER BY id)) FROM patients WHERE notes = '$sentinel'")"
[ "$source_count" = "1" ] || fail "Synthetic sentinel was not created exactly once."

pg_dump "$SOURCE_DATABASE_URL" --format=custom --no-owner --no-privileges --file="$dump_file"
dropdb --if-exists --maintenance-db="$TARGET_ADMIN_URL" "$TARGET_DB"
createdb --maintenance-db="$TARGET_ADMIN_URL" "$TARGET_DB"
pg_restore --exit-on-error --dbname="$TARGET_DATABASE_URL" --no-owner --no-privileges "$dump_file"

target_count="$(psql "$TARGET_DATABASE_URL" -At -v ON_ERROR_STOP=1 -c "SELECT count(*) FROM patients WHERE notes = '$sentinel'")"
target_checksum="$(psql "$TARGET_DATABASE_URL" -At -v ON_ERROR_STOP=1 -c "SELECT md5(string_agg(first_name || '|' || last_name || '|' || email || '|' || notes, ',' ORDER BY id)) FROM patients WHERE notes = '$sentinel'")"
[ "$target_count" = "$source_count" ] || fail "Restored sentinel row count differs."
[ "$target_checksum" = "$source_checksum" ] || fail "Restored sentinel checksum differs."

echo "PASS: synthetic test backup restored into a separate database; row count and checksum match."
