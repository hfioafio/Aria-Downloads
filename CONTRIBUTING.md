# Contribution guidelines

This repository is a distribution surface for Aria. Keep it intentionally small and predictable.

## Scope

Appropriate content:

- public release notes;
- update manifests and checksums;
- download documentation;
- public support or installation documentation.

Do not place application source code, local build directories, private signing material, API keys, development notes or unrelated projects in this repository.

## Release hygiene

- Keep version numbers consistent across manifests, notes and published assets.
- Verify checksums before publishing them.
- Do not replace an existing published artifact silently; publish a new version instead.
- Keep Apple Silicon and Intel artifacts clearly distinguishable.
- Never commit certificates, private keys, notarization credentials or temporary build output.

## Documentation

Write concise user-facing documentation. Internal build procedures and maintenance discussions belong in the private source repository, not here.
