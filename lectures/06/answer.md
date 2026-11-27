# Lecture 06 answers

## Exercises

<!-- Paste the original [tool call] lines. Leave unfinished steps blank. -->

- Tool name in STEP 1 — glossary_search_glossary (the first line of `uv run python -m app.mcp_agent --list-tools` was `[server] glossary: starting with command (uv run python -m app.mcp_server)`; the agent from Lecture 05 listed `search_materials` instead)
- STEP 2 [tool call] — glossary_search_glossary({'query': 'homework levels'})
- STEP 3 [tool call] — fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 [tool call] — aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Amazon S3 versioning overview'})
- Observations and questions —
  - **STEP 2:** `[usage]` showed 2 model responses: one that called the tool and one that read the result. The answer matched the glossary entry "3 homework levels" (Basic, Implementation, Advanced, and completing any one is enough).
  - **STEP 3:** With `fetch` added, the list had 2 tools (`glossary_search_glossary`, `fetch_fetch`). The model read the page and gave three lines. The server's log showed that it first requested `robots.txt`, then followed a redirect to the page's markdown version, which matches the "respects robots.txt" default in the instructions.
  - **STEP 4:** With `aws` added, the list had 7 tools: the 2 above plus 5 with the prefix `aws_` (`aws_aws___read_documentation`, `aws_aws___search_documentation`, `aws_aws___list_regions`, `aws_aws___get_regional_availability`, `aws_aws___retrieve_skill`). The model chose `search_documentation` itself, in one call. `[usage]` input tokens grew from 615 (STEP 2, 1 tool) to 6,253 (STEP 4, 7 tools). Part of that comes from the search result that AWS returned and part from the 6 added tool descriptions. I did not separate the two, so I cannot say how much each tool costs.
  - **Tool names:** The prefix is the server name and an underscore. The AWS tools have two underscores after `aws` and three in the middle (`aws_aws___…`), because AWS's own tool names are `aws___search_documentation`. This looks odd and I did not look into why AWS uses it.
  - **Description of `fetch_fetch`:** The description that the fetch server sends to the model includes the sentence "Although originally you did not have internet access, and were advised to refuse and tell the user this, this tool now grants you internet access." That is an instruction aimed at the model, written by the server's author. It is harmless here, but it shows that a server's tool descriptions go straight into the model's context, so an untrusted server could put anything there. I checked that this package is published by Anthropic on PyPI (version 2026.11.11 exists) before using it.
  - **Remote server:** The AWS question was sent to AWS. I used a general documentation question, with nothing private in it.
  - **Environment:** `uvx` downloaded the fetch server without problems when I ran the commands with `UV_SYSTEM_CERTS=1` and `UV_NO_SYNC=1` set. I do not know whether `UV_SYSTEM_CERTS` fixed the earlier TLS errors on this machine or whether those were intermittent.
  - **Two things I did not check:** Whether the model would use `fetch` for a URL without being told to (the troubleshooting table says it may skip it), because it called the tool on the first try. And whether `[usage]` counts the tokens of the tool descriptions separately.

## Homework

<!-- Complete one of the Basic, Implementation, or Advanced levels. -->

- Level attempted (Basic / Implementation / Advanced) — Advanced
- What you did — I researched how Gemini CLI configures MCP servers and compared it with `app/mcp_servers.json`.
  - Date checked: 2026-11-26.
  - Official documentation: "MCP servers with Gemini CLI", https://geminicli.com/docs/tools/mcp-server/ (the whole page, including the `gemini mcp add` section).
  - Method: documentation only, as the homework allows. Gemini CLI is not installed on my machine, so I did not run it or write a real `settings.json`. I read `app/mcp_servers.json` and the part of `app/mcp_agent.py` that loads it (fields it reads, tool-name prefix).
- Results —

| Question | Course (`app/mcp_servers.json`) | Gemini CLI (official docs) |
|---|---|---|
| Where does the configuration go? | One file, `app/mcp_servers.json`, with the top-level key `mcpServers`. Edited by hand. | The `mcpServers` object inside `settings.json`. Either edit the file or run `gemini mcp add`. Other settings (for example `mcp.allowed` and `mcp.excluded`) live in the same file. |
| Start a server with a command | `"command"` plus `"args"` (and `"env"`). The glossary server is `uv run python -m app.mcp_server`. | The same `"command"` and `"args"`, plus `"env"`, `"cwd"` and `"timeout"` (default 600,000 ms). The command form is `gemini mcp add <name> <command> [args...]`. Stdio is the default transport. |
| Connect by URL | `"url"`. The `aws` example is `{"url": "https://knowledge-mcp.global.api.aws"}`. One key for every remote server. | Two keys: `"url"` for an SSE endpoint and `"httpUrl"` for streamable HTTP. On the command line, `--transport sse` or `--transport http`. Custom `"headers"` are allowed, and OAuth 2.0 is supported for remote servers. |
| Scope | Only this project. The file is inside the repository. | Two levels: user (`~/.gemini/settings.json`, all projects) and project (`.gemini/settings.json`, this project). `gemini mcp add -s user|project` chooses one; the default is `project`. |

Other differences I found on the page:
  - **Tool names.** Gemini CLI names every MCP tool `mcp_{serverName}_{toolName}`. The course agent uses `{serverName}_{toolName}` (for example `glossary_search_glossary`). Both prefix the server name so equal tool names on different servers do not collide. If two servers share an alias and a tool name in Gemini CLI, the last one overwrites the other.
  - **Control over tools.** Gemini CLI can allow or block individual tools per server (`includeTools`, `excludeTools`). It can also skip confirmation prompts for a server (`"trust": true`). The course file has none of these, so every tool a server publishes reaches the model.
  - **Secrets.** Gemini CLI removes variables such as `GEMINI_API_KEY` and anything matching `*TOKEN*`, `*SECRET*` or `*KEY*` from the environment it gives to a server. A variable has to be listed in `"env"` (for example `"$MY_TOKEN"`) to pass through. In the course code I read, the `env` value is handed straight to the subprocess, and I did not check whether it filters the parent environment.
  - **Validation.** The course loader raises an error if a server has neither `command` nor `url` and reads only `command`, `args`, `env` and `url`. I did not look for Gemini CLI's validation rules beyond the listed keys.
- Observations and questions —
  - The core idea is the same in both: a named entry with either a command (stdio) or a URL (remote). The course file is a smaller subset of the Gemini CLI format. The `mcpServers` / `command` / `args` / `env` part looks the same, so I expect the glossary entry to work in Gemini CLI unchanged. I did not test that.
  - Questions I could not answer from the page: how does Gemini CLI decide between a user and a project entry with the same name? How does the course client choose between SSE and streamable HTTP for a plain `"url"`? The loader passes the URL to the client in `legacy` mode, and I did not read how the client decides.
  - `trust`, tool filtering and secret filtering matter for safety. The course file has no setting for any of them. I did not check whether the course agent asks for approval before calling a tool, so I cannot say how a malicious server would be handled.
  - Why Gemini CLI: I already use it on another machine for development. In my experience it is intuitive, easy to use, and works very autonomously on development tasks. The one thing I dislike is that it does not show the changes (the diff) by default. That is understandable for a command-line interface, but I would like an option to see them. This is my own opinion from using it. It is not based on the MCP documentation, and I have not used MCP servers with Gemini CLI.
  - How I speed up development with it: I use its command-line switches and its subagent orchestration, configured as described in the official documentation ([CLI cheatsheet](https://geminicli.com/docs/cli/cli-reference/) and [Subagents](https://geminicli.com/docs/core/subagents/), checked 2026-11-26).
    - Switches: `--approval-mode` to choose how much it asks before acting (`default`, `auto_edit` to apply edits without asking, `yolo` to approve everything, `plan` to plan first; Shift+Tab cycles the modes in a session). `-m` / `--model` to pick the model (`auto`, `pro`, `flash`, `flash-lite`), using a faster one for simple tasks. `-p` / `--prompt` to run a single prompt without the interactive session, for scripts. `-r latest` to resume the last session. `-w` / `--worktree` to work in a separate git worktree (experimental; needs `experimental.worktrees: true` in settings). `--sandbox` to run in a sandbox for safer execution. The docs mark `--yolo` / `-y` as deprecated in favor of `--approval-mode=yolo`.
    - Orchestration: the main agent delegates tasks to subagents, each with its own context window, which keeps the main conversation small. The built-in ones are `codebase_investigator` (analyzes code), `generalist` (multi-file changes, long command output), `cli_help` and `browser_agent`. I can force one with `@name` at the start of a prompt (for example `@generalist`), and tune them in `settings.json` under `agents.overrides` (for example a different model or more turns). Remote subagents over the Agent-to-Agent (A2A) protocol are also supported.
    - Relation to MCP: none of these change how MCP servers are configured. The flag `--allowed-mcp-server-names` is the only one that touches MCP, by limiting which configured servers may connect.
  - AI tool use: an AI coding assistant (Kiro) fetched and read the documentation page and drafted the table above. I did not run Gemini CLI on this machine or test any MCP configuration, so read the table as a documentation summary, not as tested results.
