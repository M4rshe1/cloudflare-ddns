# M4rshe1/cloudflare-ddns

## Description

A simple script to update a Cloudflare DNS record with your current public IP address.

## environment variables

- `CF_API_TOKEN` - The API token associated with your Cloudflare account
- `CF_ACC_EMAIL` - The email address associated with your Cloudflare account
- `CF_ZONE_ID` - The ID of the zone that contains the record you want to update
- `CF_DNS_NAME` - The name of the record you want to update
- `IP_PROVIDER` - The IP address provider to use (defaults to `ipify`) (options: `ipify`,  `icanhazip`, `myip`)
- `CRON_SCHEDULE` - The schedule for running the script (defaults to `*/5 * * * *`)
- `PROXY` - Whether to proxy the record through Cloudflare (defaults to `false`)
- `TTL` - The TTL for the record (defaults to `3600`)

