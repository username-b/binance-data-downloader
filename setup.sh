#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '==> %s\n' "$1"
}

fail() {
  printf 'Error: %s\n' "$1" >&2
  exit 1
}

require_sudo() {
  if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
    command -v sudo >/dev/null 2>&1 || fail "sudo not found. Run the script as root or install sudo."
    SUDO="sudo"
  else
    SUDO=""
  fi
}

detect_pkg_manager() {
  if command -v apt-get >/dev/null 2>&1; then
    PKG_MANAGER="apt"
    return
  fi

  if command -v dnf >/dev/null 2>&1; then
    PKG_MANAGER="dnf"
    return
  fi

  if command -v yum >/dev/null 2>&1; then
    PKG_MANAGER="yum"
    return
  fi

  fail "Supported package managers: apt, dnf, yum."
}

install_docker() {
  if command -v docker >/dev/null 2>&1; then
    log "Docker is already installed"
    return
  fi

  log "Installing Docker Engine"

  case "$PKG_MANAGER" in
    apt)
      $SUDO apt-get update
      $SUDO apt-get install -y ca-certificates curl
      curl -fsSL https://get.docker.com | $SUDO sh
      ;;
    dnf)
      $SUDO dnf install -y dnf-plugins-core curl
      $SUDO dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
      $SUDO dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
      ;;
    yum)
      $SUDO yum install -y yum-utils curl
      $SUDO yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
      $SUDO yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
      ;;
  esac
}

enable_docker() {
  log "Enabling and starting Docker"
  $SUDO systemctl enable docker
  $SUDO systemctl start docker
}

wait_for_docker() {
  local retries=${1:-20}
  local delay=${2:-2}

  for ((i=1; i<=retries; i++)); do
    if $SUDO docker info >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
  done

  return 1
}

add_user_to_docker_group() {
  local target_user="${SUDO_USER:-${USER:-}}"

  if [[ -z "$target_user" || "$target_user" == "root" ]]; then
    return
  fi

  if id -nG "$target_user" | grep -qw docker; then
    return
  fi

  log "Adding $target_user to docker group"
  $SUDO usermod -aG docker "$target_user"
  log "Log out and back in to apply group membership."
}

has_compose_file() {
  [[ -f docker-compose.yml || -f compose.yml || -f compose.yaml ]]
}

start_compose_app() {
  if ! has_compose_file; then
    log "Compose file not found. Docker is installed and running; skipping app startup."
    return
  fi

  if [[ -f docker-compose.yml ]] && grep -q 'env_file:' docker-compose.yml && [[ ! -f .env ]]; then
    fail "docker-compose.yml references env_file, but .env is missing."
  fi

  log "Building and starting containers"
  $SUDO docker compose up -d --build
  $SUDO docker compose ps
}

main() {
  require_sudo
  detect_pkg_manager
  install_docker
  enable_docker

  wait_for_docker || fail "Docker Engine is not responding. Check: systemctl status docker"

  add_user_to_docker_group
  start_compose_app

  log "Done"
}

main "$@"
