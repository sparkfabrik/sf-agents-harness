# References for short descriptions

These sources inform our rules. They do not prescribe our word limits or a mandatory MR template.

- [Google Engineering Practices: Writing good CL descriptions](https://google.github.io/eng-practices/review/developer/cl-descriptions.html): Start with a specific summary that stands alone. Include necessary context and update the description when the change evolves.
- [GitHub: How to write the perfect pull request](https://github.blog/developer-skills/github/how-to-write-the-perfect-pull-request/): Explain the purpose for readers unfamiliar with the task. Identify specific feedback needed when there is a concrete review question.
- [Nielsen Norman Group: How users read on the web](https://www.nngroup.com/articles/how-users-read-on-the-web/): Help readers scan with meaningful headings, bullets, highlighted keywords and objective language. This is general web reading research, not evidence about PR review speed.

## Our adaptation

Lead with what changes. Keep one sentence of context only when a reviewer needs it to understand the change. Leave investigation history and implementation walkthroughs out.

Choose formatting that fits the change: one sentence for a small fix, bullets for distinct changes, and visible required actions or useful verified results. Examples illustrate choices; they are not templates.

The default word limits are team conventions. Essential information takes priority over compression. Review the final description against the final diff and current evidence.

These references support maintenance of the skill. Routine drafting needs only the rules in `SKILL.md`; it does not require loading this file or fetching the linked pages.
