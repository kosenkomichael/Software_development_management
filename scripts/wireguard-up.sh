#!/usr/bin/env bash
set -euo pipefail
set +x
umask 077

: "${WG_ENDPOINT:?WG_ENDPOINT is required}"
: "${WG_PEER_PUBLIC:?WG_PEER_PUBLIC is required}"
: "${WG_ADDRESS:?WG_ADDRESS is required}"
: "${WG_ALLOWED_IPS:?WG_ALLOWED_IPS is required}"
: "${WG_PRIVATE_KEY:?WG_PRIVATE_KEY is required}"

sudo apt-get update -qq
sudo apt-get install -y -qq wireguard-tools
sudo install -d -m 700 /etc/wireguard

tmp=$(mktemp -p /dev/shm)
trap 'rm -f "$tmp"' EXIT
{
  printf '[Interface]\n'
  printf 'PrivateKey = %s\n' "$WG_PRIVATE_KEY"
  printf 'Address = %s\n' "$WG_ADDRESS"
  printf '\n[Peer]\n'
  printf 'PublicKey = %s\n' "$WG_PEER_PUBLIC"
  printf 'Endpoint = %s\n' "$WG_ENDPOINT"
  printf 'AllowedIPs = %s\n' "$WG_ALLOWED_IPS"
  printf 'PersistentKeepalive = 25\n'
} > "$tmp"
chmod 600 "$tmp"
sudo install -m 600 -o root -g root "$tmp" /etc/wireguard/wg0.conf

if ! sudo wg-quick up wg0 >/dev/null 2>/tmp/wg-up.err; then
  echo "wg-quick up failed"
  sed -E 's/=[^[:space:]]*/=<REDACTED>/g' /tmp/wg-up.err || true
  exit 1
fi

if ! sudo wg show wg0 latest-handshakes | awk '$2 > 0 {found=1} END {exit !found}'; then
  echo "WireGuard: no handshake"
  exit 1
fi
echo "WireGuard: up"
