#!/usr/bin/env python3
"""Generate SSH configuration and authorized_keys files from config.yml"""

import yaml
import sys
import json
import os
from pathlib import Path


def load_config():
    """Load and validate the configuration."""
    with open('config.yml') as f:
        config = yaml.safe_load(f)
    
    # Validate root_key is present and valid
    if 'root_key' not in config or 'public' not in config['root_key']:
        print("Error: root_key.public is required in config.yml", file=sys.stderr)
        sys.exit(1)
    
    root_key_path = Path(config['root_key']['public'])
    if not root_key_path.exists():
        print(f"Error: Root key file not found: {root_key_path}", file=sys.stderr)
        sys.exit(1)
    
    root_key_content = root_key_path.read_text().strip()
    if not root_key_content:
        print(f"Error: Root key file is empty: {root_key_path}", file=sys.stderr)
        sys.exit(1)
    
    return config


def resolve_access(person_config, groups):
    """Resolve which servers a person can access."""
    servers = set()
    access = person_config.get('access', [])
    
    # Handle both list and dict formats
    if isinstance(access, list):
        items = access
    else:
        items = access.get('servers', []) + access.get('groups', [])
    
    for item in items:
        servers.update(groups.get(item, [item]))
    
    return servers


def get_keys(key_data):
    """Extract SSH keys from various formats."""
    if isinstance(key_data, str):
        return [key_data] if key_data.startswith('ssh-') else [Path(key_data).read_text().strip()]
    
    keys = []
    for entry in key_data:
        if entry.startswith('ssh-'):
            keys.append(entry.strip())
        else:
            keys.append(Path(entry).read_text().strip())
    return keys


def generate_authorized_keys(server_name, config):
    """Generate authorized_keys content for a server."""
    lines = []
    groups = config.get('groups', {})
    
    # Add keys from people with access
    for person, person_config in config['people'].items():
        if not person_config.get('enabled', True):
            continue
        if server_name not in resolve_access(person_config, groups):
            continue
        
        lines.append(f"# {person}")
        lines.extend(get_keys(person_config['keys']))
    
    # Add root key (required)
    lines.append("# root_key (deployment)")
    lines.extend(get_keys(config['root_key']['public']))
    
    return '\n'.join(lines) + '\n' if lines else ''


def generate_ssh_config(config):
    """Generate SSH config from server definitions."""
    lines = []
    for name, srv in config['servers'].items():
        if not srv.get('enabled', True):
            continue
        lines.append(f"Host {name}")
        lines.append(f"    HostName {srv['hostname']}")
        lines.append(f"    User {srv['user']}")
        if 'port' in srv:
            lines.append(f"    Port {srv['port']}")
        lines.append("")
    return '\n'.join(lines)


def main():
    """Main entry point - called by GitHub Actions."""
    config = load_config()

    # Create generated directory
    output_dir = Path('generated')
    output_dir.mkdir(exist_ok=True)

    # Generate SSH config
    config_file = output_dir / 'config'
    config_file.write_text(generate_ssh_config(config))
    print(f"✓ Generated {config_file}")
  
    # Generate authorized_keys for all enabled servers
    for name, srv in config['servers'].items():
        if not srv.get('enabled', True):
            continue

        content = generate_authorized_keys(name, config)
        output = output_dir / f'authorized_keys.{name}'
        output.write_text(content)
        print(f"✓ Generated {output}")
    
    # Output server list for GitHub Actions matrix
    servers = [
        {'name': name, 'restart_service': srv.get('restart_service', '')}
        for name, srv in config['servers'].items()
        if srv.get('enabled', True)
    ]
    
    output = f"servers={json.dumps(servers)}"
    print(output)
    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(output + '\n')


if __name__ == '__main__':
    main()
