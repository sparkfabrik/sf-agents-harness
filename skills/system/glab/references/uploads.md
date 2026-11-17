# File uploads (images, attachments)

No `glab` subcommand uploads a file for a description or comment, and `glab release upload` only handles release assets. Use `glab api --form` with the project uploads API. It needs `glab` 1.91 or later and uses the stored login, so no token is read or printed.

Before the first upload to a project, read its visibility and media setting with one call. Do it once per project per session and reuse the result for every later upload there, never once per image. If you already resolved the project path in this session with the lookup from "Fully-qualified references", read the fields from that response instead of calling again.

For a `private` or `internal` project, upload only when `enforce_auth_checks_on_uploads` is `true`. When it is `false`, `null`, or missing (the field can be hidden from your role), do not upload: use a text preview, or give the user the image path to attach.

```bash
# One call per project per session: path, visibility and media setting together
GITLAB_HOST=<hostname> glab api projects/:id | jq '{path_with_namespace, visibility, enforce_auth_checks_on_uploads}'

# Inside a clone of the project
GITLAB_HOST=<hostname> glab api projects/:id/uploads --form "file=@path/to/image.png" | jq -r '.markdown'
# ![image](/uploads/<hash>/image.png)

# Outside a clone: URL-encode the project path
GITLAB_HOST=<hostname> glab api "projects/group%2Fproject/uploads" --form "file=@path/to/image.png" | jq -r '.markdown'
```

- **`--form`, not `-F`.** `--form` sends `multipart/form-data` and switches the method to POST. `-F file=@path` reads the file into a JSON string field and does not upload it.
- **No `curl` and no token.** Never extract the token to upload with another tool, and never run `glab auth status -t`: it prints the token.
- **Response.** The JSON holds `markdown`, ready to paste, and `url`, a path that resolves only inside this project. Replace the default alt text with a description of what the image shows.
- **Visibility.** In a private or internal project the file is visible only to people who can view the project when "Require authentication to view media files" (`enforce_auth_checks_on_uploads`) is on. When it is off, anyone with the link can open the file. In a public project anyone with the link can always open it, even when it is attached to a confidential issue.
- **Before uploading.** Open the file and remove secrets, personal data, and customer data. An uploaded file is hard to delete.
- **No other host.** Never use an external image host, a snippet, a release asset, or a commit on the branch to show an image.

Use the returned Markdown in an MR or issue description or comment:

```markdown
![Login form with the validation message](/uploads/<hash>/image.png)
```

When adding the image to an existing description, follow the re-fetch rule from "Reviewing and managing MRs": fetch the current raw description first and append to it, because `--description` replaces the whole body.

---
