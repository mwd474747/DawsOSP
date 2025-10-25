This directory mounts into `/app/ledger` for containers that need access to the Beancount truth spine.

- Populate it with the demo ledger repository (or point to your production clone) before starting Docker services.
- Keep commits out of source control if your ledger includes sensitive data; use placeholders or a sanitized copy for development.
