#!/usr/bin/env bash

usage() {
  echo "Usage: $(basename "$0") [--debug] [--timestamp] [--config FILE] [--dry-run]"
}

_log() {
  local color="$1"
  shift
  local msg="$*"
  local ts

  if [[ -n "$TIMESTAMP_LOGS" ]]
  then
    ts="$(date '+\e[90m[%T.%N]\e[39m ')"
  fi

  echo -e "${ts}\e[${color}m${msg}\e[0m" >&2
}

log_success() {
  _log 32 "$@"
}

log_error() {
  _log 31 "$@"
}

log_info() {
  _log 34 "$@"
}

log_debug() {
  if [[ "$LOG_LEVEL" != "debug" ]]
  then
    return
  fi
  _log 35 "$@"
}

in-zoom-meeting() {
  local pid
  pid="$(is-running 'zoom zoommtg://')"

  # There should be a window named "Zoom Meeting"
  if [[ -n "$pid" ]] && wmctrl -l | grep -qi "zoom meeting"
  then
    echo "$pid"
    return 0
  fi

  return 1
}

is-running() {
  local res
  res="$(pgrep --full --list-full --ignore-case --oldest "${1}" 2>/dev/null)"
  local rc="$?"
  if [[ "$rc" -ne 0 ]]
  then
    return "$rc"
  fi

  # Return PID
  awk '{ print $1; exit }' <<< "$res"
}

is-running-for() {
  local app="$1"
  local pid=$(is-running "$1")

  if [[ -z "$pid" ]]
  then
    log_error "$app is not currently running"
    return 2
  fi

  get-runtime "$pid"
}

get-runtime() {
  ps -o etimes= -p "$1"
}

runtime-self() {
  get-runtime "$$"
}

was-started-after-us() {
  local app="$1"
  local pid

  # Check if $1 is a PID
  if [[ "$app" =~ ^[0-9]+$ ]]
  then
    pid="$app"
  else
    pid=$(is-running "$app")
  fi

  if [[ -z "$pid" ]]
  then
    log_error "Unable to find PID for $app"
  fi

  local runtime_app
  local runtime_self

  runtime_app="$(get-runtime $pid)"
  runtime_self="$(runtime-self)"

  log_debug "🕰️ Runtimes: $runtime_app <? $runtime_self"
  [[ "${runtime_app}" -lt "${runtime_self}" ]]
}

array-contains() {
  local e match="$1"
  shift

  for e
  do
    [[ "$e" == "$match" ]] && return 0
  done

  return 1
}

should-trigger-script() {
  local app="$1"
  local pid="$2"
  local previous_state="$3"

  if [[ -z "$previous_state" ]]
  then
    log_debug "🤷 Not triggering start script since previous state is unknown."
    return 1
  fi

  if [[ "$previous_state" == "running" ]]
  then
    log_debug "✋ Not triggering start script since we already did this once"
    return 1
  fi

  local -a skip_checks
  mapfile -t skip_checks < <(config-get ".apps.${app}.scripts.skip-checks")

  if ! array-contains "runtime" "${skip_checks[@]}"
  then
    was-started-after-us "$pid"
  fi
}

was-just-started() {
  local pid="$1"
  local runtime

  runtime="$(get-runtime $pid)"

  [[ $(( runtime - SLEEP_INTERVAL )) -lt 0 ]]
}

window-exists() {
  wmctrl -l | grep -iq "$1"
}

app-check() {
  local app="$1"
  local pid
  local name
  local process_name
  local win_name

  name="$(config-get ".apps.${app}.name")"
  process_name="$(config-get ".apps.${app}.process_name" "$app")"
  window_title="$(config-get ".apps.${app}.window_title")"

  if ! pid=$(is-running "$process_name")
  then
    log_debug "🦽 App is *not* running: $name"
    return 1
  fi

  if [[ -n "$window_title" ]] && ! window-exists "$window_title"
  then
    log_debug "🙈 App is *not* running: $name (PID exists, but no visible window)"
    return 1
  fi

  log_debug "🆙 ${name} is running."
  echo "$pid"
}

app-run-scripts() {
  local app="$1"
  local event="$2" # start or stop

  local script
  local -a scripts

  mapfile -t scripts < <(config-get ".apps.${app}.scripts.${event}")

  for script in "${scripts[@]}"
  do
    log_debug "🚀 Running ${script}"
    eval ${script} &
  done
}

app-run-start-scripts() {
  app-run-scripts "$1" start
}

app-run-stop-scripts() {
  app-run-scripts "$1" stop
}

config-path() {
  local xdg="${XDG_CONFIG_HOME:-${HOME}/.config}"

  local c
  for c in "${CONFIG_FILE}" \
           "${xdg}/tasker-for-linux/config.yaml" \
           "${PWD}/config.yaml"
  do
    if [[ -r "$c" ]]
    then
      echo "$c"
      return
    fi
  done

  log_error "😖 Config file path could not be determined"
  return 1
}

config-get-raw() {
  local conf

  if ! conf="$(config-path)"
  then
    log_error "Config file not found or inacessible: $conf"
    return 3
  fi

  yq --exit-status --no-colors eval "$*" "$conf" 2>/dev/null
}

config-get() {
  local res rc
  local default_value="$2"

  res="$(config-get-raw "$1")"
  rc="$?"

  if [[ "$rc" -ne 0 ]]
  then
    return "$rc"
  fi

  # Check if result is a list
  if [[ "$res" =~ ^"- "* ]]
  then
    # Flatten list
    res="$(sed 's/^- //' <<< "$res")"
  fi

  echo "${res:-${default_value}}"
}

config-get-bool() {
  config-get "$* == true" >/dev/null
}

config-list-apps() {
  config-get '.apps | keys'
}

main-loop() {
  local -a apps
  local -A app_states
  local a
  local previous_state
  local pid
  local sleep_interval="${SLEEP_INTERVAL}"

  mapfile -t apps < <(config-list-apps)

  if [[ -z "$sleep_interval" ]]
  then
    sleep_interval=$(config-get .sleep_interval 2)
  fi

  log_info "📄 Config file: $(config-path)"
  log_info "👮 Starting process watchdog for: ${apps[*]}"

  while true
  do
    for a in "${apps[@]}"
    do
      previous_state="${app_states[$a]}"

      # Check if "zoom: true" is set for this app
      if config-get-bool ".apps.${a}.zoom"
      then
        pid=$(in-zoom-meeting)
      else
        pid="$(app-check "$a")"
      fi

      if [[ -n "$pid" ]]
      then
        # App is running
        if should-trigger-script "$a" "$pid" "$previous_state"
        then
          log_success "🌞 $a just started"
          app-run-start-scripts "$a"
        fi

        app_states[$a]=running
      else
        # App is *not* running
        if [[ "$previous_state" == "running" ]]
        then
          log_success "🛑 $a just stopped!"
          app-run-stop-scripts "$a"
        fi
        app_states[$a]=stopped
      fi
    done

    log_debug "💤 Sleeping for $sleep_interval seconds..."
    sleep "$sleep_interval"
  done
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]
then
  CONFIG_FILE="${CONFIG_FILE}"
  DRY_RUN="${DRY_RUN}"
  TIMESTAMP_LOGS="${TIMESTAMP_LOGS}"
  LOG_LEVEL="${LOG_LEVEL:-info}"
  SLEEP_INTERVAL="${SLEEP_INTERVAL}"

  DISPLAY="${DISPLAY:-:0}"
  WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"

  while [[ -n "$*" ]]
  do
    case "$1" in
      -h|--help)
        usage
        exit 0
        ;;
      -d|--debug)
        LOG_LEVEL=debug
        shift
        ;;
      -k|--dry-run|--dry|--dryrun)
        DRY_RUN=1
        shift
        ;;
      -c|--conf|--config)
        if [[ -z "$2" ]]
        then
          log_error "❌ Missing config file arg."
          exit 2
        fi
        CONFIG_FILE="$2"
        shift 2
        ;;
      -t|--timestamp|--ts|-ts)
        TIMESTAMP_LOGS=1
        shift
        ;;
      --usr1|-1|--signal|--sig|--restart|--reload|-r|reload|restart|usr1)
        log_debug pkill -USR1 --full --oldest "^bash.*$(basename "$0")"
        pkill -USR1 --full --oldest "^bash.*$(basename "$0")"
        exit "$?"
        ;;
      *)
        log_error "Unknown option: $1"
        usage >&2
        exit 2
        ;;
    esac
  done

  trap 'log_info "🚨 USR1 caught. Restarting."; main-loop' USR1
  main-loop
fi
