# Contributing

1. Add or change a public macro with a corresponding integration case.
2. Put warehouse-specific SQL behind adapter dispatch.
3. Do not fall back from safe conversion to ordinary `cast()`.
4. Validate enum-like macro arguments at compile time.
5. Run `make check` before opening a pull request.
6. Update the README catalogue and changelog when the public API changes.

