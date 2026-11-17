# Other hosts and logging in

## Targeting a host different from the repo's git remote (use `--hostname` for `glab api`)

Inside a git repo, `glab` resolves the host from the repo's git remote, and that resolution can **override `GITLAB_HOST`**. So when you are inside a repo on host A (for example a self-hosted instance) but need to query host B (for example `gitlab.com`), `GITLAB_HOST=B glab api ...` may silently still hit host A and return `404 Project Not Found` for a project that exists on B.

For `glab api`, pass the **`--hostname` flag** instead. It is authoritative: it beats both the repo remote and `GITLAB_HOST`.

```bash
# Inside a self-hosted repo, querying a public gitlab.com project: CORRECT
glab api --hostname gitlab.com "projects/gitlab-org%2Fterraform-provider-gitlab/issues/6841"

# GITLAB_HOST can lose to the repo remote for a cross-host api call: do NOT rely on it
GITLAB_HOST=gitlab.com glab api "projects/gitlab-org%2Fterraform-provider-gitlab/..."   # may 404
```

Telltale sign you hit the wrong host: a `404 Project Not Found` for a project you know exists. It is easy to miss when your username exists on both instances, because `glab api user` then succeeds on either host and masks which one answered. Confirm the host with `glab api --hostname <host> user` (compare the returned user id), not just the username.

## Logging in

When authentication is confirmed to be invalid, present the user with these options:

### Option 1: OAuth login (preferred -- more secure, tokens auto-refresh)

```bash
glab auth login --hostname <hostname>
# Select "Web" → browser opens → authorize → done
```

If OAuth fails (no OAuth app configured on the instance), fall back to a PAT.

### Option 2: Personal Access Token

Check git protocol to recommend minimal scopes:

- **SSH users** (`git@...` remote): `api` scope is sufficient
- **HTTPS users** (`https://...` remote): `api` + `write_repository`

Tell the user to generate a token at: `https://<hostname>/-/user_settings/personal_access_tokens?scopes=api,write_repository` — recommend a short expiry (30-90 days).

```bash
glab auth login --hostname <hostname> --token <token>
```

### Option 3: Skip the operation

glab stores credentials in the OS keyring by default. **Never pass `--insecure-storage`**: it stores the token in plaintext config.
