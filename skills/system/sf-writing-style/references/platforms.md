# Platform formatting

Use this reference when the text will be rendered by GitHub, GitLab, or Slack. The parent `sf-writing-style` skill still decides what the text says; this file only covers how each platform displays it.

## GitHub and GitLab

Both render GitHub-flavored Markdown with headings, tables, task lists, and fenced code.

- **References link only when bare.** `#42` on GitHub, `#42` and `!15` on GitLab, and `@user` mentions become links. Inside backticks they render as plain code, so keep them out of code formatting.
- **Cross-project references need the full path.** A short reference resolves only inside its own repository or project. Write `owner/repo#42` on GitHub and `group/subgroup/project#42` on GitLab when the item lives elsewhere, or when the text may be read from a board, notification, or another project.
- **Task lists track work.** Use `- [ ]` items for tasks and acceptance criteria that someone will tick off. Use plain bullets for facts.
- **Templates come first.** When a project has issue or PR/MR templates, keep their required headings and fill them. Remove hint text and placeholders that do not apply.
- **Parent and child work.** When the tracker has no native parent-child feature, use one parent issue whose task list holds fully-qualified references to the child issues, write dependencies as text such as "blocks #43", and link each child back to the parent.
- **Long detail can collapse.** Use `<details><summary>Logs</summary> ... </details>` for supplied material a reader may need but should not scroll past.

## Slack

Slack formatting depends on how the message is sent. Check the sending tool's documentation before choosing syntax.

- **Standard Markdown tools.** Some connectors accept standard Markdown (`**bold**`, `[text](url)`, lists, and sometimes tables) and convert it. Use tables only when the tool documents table support.
- **Raw `mrkdwn`.** Webhooks and the raw API use Slack's own syntax: `*bold*`, `_italic_`, `~strike~`, `` `code` ``, fenced code blocks, `>` quotes, and `<https://example.com|link text>`. Headings and tables do not render, so use a bold first line and short lists instead.
- **Lead line.** Start with one bold line that states the update, because notifications and channel previews show only the first line.
- **Threads.** Post follow-ups to a thread under the original message. Also send to the channel only when everyone needs the follow-up.
- **Length.** Keep a message readable without expanding it. Split long content, or link to the issue, PR/MR, or document that holds the detail.
- **Mentions.** Mention people only when they must act. Avoid channel-wide mentions unless the message is urgent for everyone.
