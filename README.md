# Server SSH Access

This repository automatically distributes "authorized_keys" files to servers.

On a push to this repository, all authorized_keys files are updated on all servers.

## Usage

1. find or create the key you want to add (e.g. `~/.ssh/id_rsa.pub`)
2. add the key to the `authorized_keys.<servername>` file in this repository (for the server you want to get access to)
3. push the changes to this repository

## Add host

1. add new host to "config" file
2. execute "ssh-keyscan -t ssh-ed25519 [-p <port>] <ip or dnsname> >> known_hosts" to add the host to known_hosts
   (alternative execute "ssh -F config <host>" to add the host to known_hosts)
4. add host to ".github/workflows/update-all.yml" file
5.  the changes to this repository
