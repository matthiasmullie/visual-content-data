I should put some effort into writing a proper README, but for now it's not  worth the effort.

There's currently only 2 scripts, and they're invoked something like this:

```sh
make START=2025-01-01T00:00:00Z STOP=2025-02-01T00:00:00Z TAG=uploadwizard uw-categories
make START=2025-01-01T00:00:00Z STOP=2025-02-01T00:00:00Z TAG=uploadwizard DAYS=7 TEXT=copyright uw-deletion-requests
```
