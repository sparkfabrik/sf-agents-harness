# adr-tools Setup Guide

Reference for installing and using [adr-tools](https://github.com/npryce/adr-tools)
by Nat Pryce.

## Installation

### macOS (Homebrew)

```bash
brew install adr-tools
```

### Linux / macOS (ASDF version manager)

```bash
asdf plugin add adr-tools
asdf install adr-tools latest
asdf global adr-tools latest
```

### Linux / macOS (from release package)

1. Download a zip or tar.gz from [releases](https://github.com/npryce/adr-tools/releases)
2. Unzip / untar the package
3. Add the `src/` subdirectory to your PATH

### Linux / macOS (from Git)

```bash
git clone https://github.com/npryce/adr-tools.git
# Add adr-tools/src/ to your PATH
```

### Windows 10 — Git Bash

1. Download a zip from [releases](https://github.com/npryce/adr-tools/releases)
2. Unzip and copy everything from `src/` into `C:\Program Files\Git\usr\bin`

### Windows 10 — WSL (Ubuntu)

Follow the "from release package" instructions above inside your WSL shell.

## Key commands

| Command                | Description                        |
| ---------------------- | ---------------------------------- |
| `adr init <directory>` | Create ADR directory with ADR 0001 |
| `adr new "Title"`      | Create a new numbered ADR          |
| `adr new -s N "Title"` | Create ADR that supersedes ADR N   |
| `adr list`             | List all ADRs                      |
| `adr help`             | Show help                          |

## Verification

After installing, verify with:

```bash
adr help
```
