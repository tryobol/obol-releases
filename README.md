# Obol self-host downloads

This repository distributes Obol releases. It contains installation guidance,
the license, and release-signing tools. The application repository is private.
You do not need a source checkout or compiler to install Obol.

**First release preparation is in progress. No downloadable release has been
published yet.** Versioned assets will appear under
[Releases](https://github.com/tryobol/obol-releases/releases) after the image,
installation and signature checks pass.

Each release provides:

- `gateway`, `control` and `web` images for Linux amd64 and arm64 at
  `ghcr.io/tryobol`, with a shared version and immutable digests.
- A pinned `docker-compose.yml`, `.env` guidance, installer and `obol` command.
- A Helm chart using the same image digests.
- `obol-bundle-<version>.tar` with offline images, deployment files and SBOMs.
- License notices, checksums and a publicly verifiable publisher signature.

Free self-hosting includes commercial use on your infrastructure and use in
your own customer applications. Private mirrors and backups are permitted.
Redistribution and offering Obol itself as a hosted service require a separate
agreement. Read [LICENSE](LICENSE) for the complete terms. Third-party and
earlier license rights remain intact. You operate and secure the installation;
paid support and Enterprise capabilities are separate.

## Verify a release

Download the chosen release assets, `RELEASE_SHA256SUMS` and
`RELEASE_SHA256SUMS.sigstore.json` from the same release. With Cosign installed:

```sh
cosign verify-blob --bundle RELEASE_SHA256SUMS.sigstore.json \
  --certificate-identity 'https://github.com/tryobol/obol-releases/.github/workflows/sign-release.yml@refs/heads/main' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com RELEASE_SHA256SUMS
sha256sum --ignore-missing -c RELEASE_SHA256SUMS
```

Every file you intend to use must appear in the checksum index and report OK.
The signed `release.json` pins the image digests. This authenticates the
publisher and the release bytes; it does not expose or independently prove
the private build process. Preserve the index and signature when transferring
an offline bundle. Verification on a disconnected host also requires Cosign
and its trusted Sigstore material to be provisioned beforehand.

The [self-host guide](https://docs.tryobol.dev/get-started/self-hosting)
describes installation, configuration, upgrades and recovery. The public
one-command installer will be enabled when the first release is available.
