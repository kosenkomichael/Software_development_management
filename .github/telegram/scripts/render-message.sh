#!/usr/bin/env bash
set -euo pipefail

COMMON_FILE=".github/telegram/messages/common.txt"
EVENT_FILE=".github/telegram/messages/${TEMPLATE:?TEMPLATE is required}"

case "$TEMPLATE" in
  build-start.txt|build-success.txt|build-failure.txt|build-cancelled.txt|\
  deploy-start.txt|deploy-success.txt|deploy-failure.txt|deploy-cancelled.txt)
    ;;
  *)
    echo "Unsupported template: $TEMPLATE"
    exit 1
    ;;
esac

if [[ ! -f "$COMMON_FILE" || ! -f "$EVENT_FILE" ]]; then
  echo "Message template not found"
  exit 1
fi

ALLOWED_VARS='$REPOSITORY $WORKFLOW $ENVIRONMENT $BRANCH $APP_REF $IMAGE_TAG $APP_SHA $COMPOSE_PROFILES $ACTOR $EVENT $RUN_NUMBER $RUN_ID $RUN_URL $SHA $TIMESTAMP'

DELIMITER="MSG_$(cat /proc/sys/kernel/random/uuid)"
MESSAGE_FILE="$(mktemp)"
trap 'rm -f "$MESSAGE_FILE"' EXIT

{
  envsubst "$ALLOWED_VARS" < "$COMMON_FILE"
  echo
  envsubst "$ALLOWED_VARS" < "$EVENT_FILE"
} > "$MESSAGE_FILE"

{
  echo "message<<$DELIMITER"
  cat "$MESSAGE_FILE"
  echo
  echo "$DELIMITER"
} >> "$GITHUB_OUTPUT"