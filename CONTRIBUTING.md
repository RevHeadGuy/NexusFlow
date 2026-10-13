# Contributing

Thanks for helping improve NexusFlow. It is an early local prototype, so clear bug reports and small, focused changes are especially useful.

## Before opening a change

- Check the README and architecture notes so proposed work matches current capabilities.
- For larger changes, open an issue first and describe the problem and intended behavior.
- Keep claims in the UI and docs aligned with what the code actually does. In particular, distinguish workflow stages from autonomous agents, and research plans from sourced research.
- Never commit credentials, local databases, or private project data.

## Local development

Follow the [README quick start](README.md#quick-start) to run the API and frontend. Before submitting a code change, run the checks relevant to the files you changed:

```bash
cd frontend
npm run lint
npx tsc --noEmit
```

For backend changes, from the repository root:

```bash
cd backend
source .venv/bin/activate
pytest
```

Include a short summary of the change and the checks you ran. If a check could not be run, say why.

## Reporting issues

Include the steps to reproduce, expected and actual behavior, relevant logs with secrets removed, and your operating system/runtime versions. Do not post credentials, private user data, or sensitive project content in an issue.
