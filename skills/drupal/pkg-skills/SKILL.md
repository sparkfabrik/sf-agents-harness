---
name: sparkfabrik-drupal-containers
description: SparkFabrik Drupal project container context. Use when running commands in local development environment, accessing Drupal from containers, or using fs-cli and make commands.
---

# SparkFabrik Drupal Container Context

Reference for working with SparkFabrik Drupal projects in local development.

## When to Use

- Running commands inside the tools container
- Accessing Drupal services from containers or host
- Using `make` targets or `fs-cli` commands
- Debugging local development environment

## Container Access

### Interactive Shell (Recommended)

```bash
# Open interactive shell in tools container
make drupal-cli

# All subsequent commands run inside the container
```

### Single Command Execution

```bash
# Run a single command in tools container
docker compose run --rm -it drupal-tools <command>

# Examples
docker compose run --rm -it drupal-tools drush status
docker compose run --rm -it drupal-tools curl -sI http://drupal-nginx/
```

## Service URLs

### From Inside the Container

When running commands inside `drupal-tools` container, services are accessible by their container name.

To discover running services:

```bash
# List running services
docker compose ps

# Example: if you see "drupal-nginx" service, access it at http://drupal-nginx
```

**Common pattern:** Service names in `docker compose ps` correspond to their hostnames inside the container network (e.g., `drupal-nginx` → `http://drupal-nginx`).

**Example:**

```bash
# From inside container
curl -sI http://drupal-nginx/node/1
```

### From Outside the Container (Host Machine)

Use `fs-cli` to get external URLs:

```bash
# List all service URLs
fs-cli pkg:get-urls

# Get Drupal URL only
fs-cli pkg:get-urls | grep drupal-nginx | awk '{ print $2 }'

# Example output: https://drupal.projectname.sparkfabrik.loc:80
```

**Example:**

```bash
# From host machine
curl -sI https://drupal.projectname.sparkfabrik.loc/
```

**Note:** Replace `projectname` with your actual project name from the `fs-cli pkg:get-urls` output.

## Common Make Targets

```bash
# List all available make targets
make help
```

## Drush Commands

From inside the container (`make drupal-cli`):

```bash
# Check status
drush status

# Clear cache
drush cr

# Run database updates
drush updb

# Export config
drush cex

# Import config
drush cim
```

## Quick Reference

| Task          | From Container              | From Host                                          |
| ------------- | --------------------------- | -------------------------------------------------- |
| Access Drupal | `curl http://drupal-nginx/` | `curl https://drupal.project.sparkfabrik.loc/`     |
| Get URLs      | N/A                         | `fs-cli pkg:get-urls`                              |
| Open shell    | N/A                         | `make drupal-cli`                                  |
| Run drush     | `drush <cmd>`               | `docker compose run --rm drupal-tools drush <cmd>` |
