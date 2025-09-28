# Omega Registry

A comprehensive home automation device registry and management system for Home Assistant.

## Overview

This repository contains the Omega Registry addon for Home Assistant, providing device management, registry operations, and automation workflows.

## Documentation

- **ADRs (Architecture Decision Records)**: See `addon/docs/adr/` for documented decisions and workflows
- **Operational topology**: see `./workspace_ops_export.yaml`

## Structure

- `addon/` - Home Assistant addon files and configuration
- `canonical/` - Registry canonical data and processing
- `scripts/` - Utility scripts and automation tools
- `_backups/` - Safety bundles and backups

## Development

1. Set up the Python environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Environment variables are loaded from `.env` (copy from template if needed)

3. See ADR documentation for workflow and operational procedures

## License

This project is licensed under the MIT License.