# Server SSH Access Management

## Overview

This repository automatically manages and distributes SSH authorized_keys files to all servers using a centralized configuration system.

All server configurations, people, and access control are managed through a single [config.yml](config.yml) file. SSH keys are stored directly in the configuration. On push to this repository, authorized_keys files are automatically generated and deployed to all enabled servers.

The script validates your [config.yml](config.yml) against [config.schema.yml](config.schema.yml) and outputs which files were generated. Each authorized_keys file includes comments showing which person owns each key.

## Change config.yml

### Add User

Add users to the `people` section with their SSH keys inline:

```yaml
people:
  username:
    keys:
      - ssh-ed25519 AAAAC3Nza... user@hostname
      - ssh-rsa AAAAB3NzaC1... user@another-machine
    access:
      - group_name    # Grant access to server groups
      - server1       # Or specific servers
    enabled: true     # Optional, defaults to true
```

**SSH Key Formats:**

Keys can be added in two ways:

1. **Inline (Recommended)** - Add keys directly in config.yml:
   ```yaml
   keys:
     - ssh-ed25519 AAAAC3Nz... user@hostname
     - ssh-rsa AAAAB3Nza... user@hostname
   ```

2. **File Reference** - Reference external key files:
   ```yaml
   keys:
     - people/username/keys.pub
   ```

Both formats can be mixed in the same configuration.

Commit and push - access will be deployed automatically!

### Add Group

Define groups in the `groups` section to manage multiple servers together:

```yaml
groups:
  all:
    - server1
    - server2
    - web1
    - web2
  webservers:
    - web1
    - web2
```

Groups make it easy to grant access to multiple servers at once by referencing the group name in a user's `access` list.

### Add Server

#### 1. Add Server Configuration

Add server to the `servers` section in [config.yml](config.yml):

```yaml
servers:
  servername:
    hostname: server.example.com    # The server's hostname or IP
    user: username                  # SSH user to connect as
    port: 22                        # Optional, defaults to 22
    restart_service: sshd           # Optional: 'ssh', 'sshd', or omit
    enabled: true                   # Optional, defaults to true
```

#### 2. Deploy Root Key to Server

You need SSH access to the server to deploy the root key:

```bash
# On your local machine, copy the root key to the server
cat rootkey.pub | ssh user@hostname 'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys'

# Verify you can connect with the root key
ssh -i rootkey user@hostname
```

#### 3. Configure SSH Security

**⚠️ IMPORTANT: Only proceed after verifying key-based access works!**

```bash
# SSH into the server
ssh user@hostname

# Edit SSH configuration
sudo nano /etc/ssh/sshd_config

# Find and change these lines:
PasswordAuthentication no
PermitRootLogin no
# exit using ctrl+x, y, enter

# Restart SSH service
sudo systemctl restart sshd  # or 'ssh' depending on your system
```

#### 4. Commit and Push

Commit and push your changes to trigger automatic deployment to the new server.

## Initial Setup

### 1. Use This Template

Create a new repository from this template.

### 2. Generate Root Key

Generate a dedicated SSH key pair for automated deployments:

```bash
# Generate the root key pair
ssh-keygen -t ed25519 -f rootkey -C "github-actions-deployment"

# This creates:
# - rootkey (private key)
# - rootkey.pub (public key)
```

### 3. Configure GitHub Secret

Add the private key to your repository secrets:

1. Copy the private key content: `cat rootkey`
2. Go to repository Settings → Secrets and variables → Actions
3. Create a new secret named `KEY_PRIVATE`
4. Paste the private key content

**⚠️ IMPORTANT:** Never commit the private key (`rootkey`) to the repository. Only `rootkey.pub` should be committed.

### 4. Update config.yml

Copy [config.yml](config.yml) template and customize with your servers, groups, and people. Ensure the `root_key` section references your public key:

```yaml
root_key:
  public: rootkey.pub
```

### 5. Install Dependencies (for local testing)

```bash
pip install pyyaml
```

### 6. Test Locally

Run the generator script to validate your configuration:

```bash
python3 generate.py

# This creates files in generated/:
# - generated/config (SSH config file)
# - generated/authorized_keys.<servername> (for each enabled server)
```

## Additional Information

### Repository Structure

```
.
├── config.yml                   # Central configuration (servers, people, groups, keys)
├── config.schema.yml            # YAML schema for validation
├── generate.py                  # Generator script (~130 lines, no arguments needed)
├── generated/                   # Generated files (gitignored)
│   ├── config                   # SSH config for all servers
│   └── authorized_keys.*        # Authorized keys for each server
├── .github/workflows/
│   ├── update-all-dynamic.yml   # Main workflow (auto-reads config.yml)
│   └── update-keys.yml          # Reusable workflow for single server
└── README.md
```

### Security Notes

- Never commit private SSH keys
- The **root key is REQUIRED** - without it, GitHub Actions cannot access servers to deploy changes
- The root key public key (`rootkey.pub`) must exist and not be empty
- The private key is stored as a GitHub secret (`KEY_PRIVATE`)
- Each server's authorized_keys is rebuilt from scratch on each deployment, with comments showing key ownership
- Disabled users (`enabled: false`) are automatically removed from all servers
- SSH keys in config.yml are public keys only - safe to commit

### Configuration Reference

Full [config.yml](config.yml) structure:

```yaml
# Server groups for easy access management
groups:
  group_name:
    - server1
    - server2

# All server definitions
servers:
  server_name:
    hostname: server.example.com
    user: username
    port: 22                    # Optional
    restart_service: sshd       # Optional: 'ssh' or 'sshd'
    enabled: true               # Optional, default true

# People and their access
people:
  person_name:
    keys:
      - ssh-ed25519 AAAAC3Nza... user@host
      - ssh-rsa AAAAB3NzaC1... user@host
    access:
      - group_name              # Grant access to all servers in group
      servers:
        - server_name           # Grant direct server access
    enabled: true               # Optional, default true

# Root deployment key (REQUIRED - used by GitHub Actions)
root_key:
  public: rootkey.pub  # Must exist and not be empty
```
