# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - Unreleased

Initial public release.

### Added

- Code generation from OpenAPI 3.x specifications to typed HTTPX clients
- Support for sync (`Client`) and async (`AsyncClient`) clients via `--async-client`
- TypedDict generation for request parameters, request bodies, and response bodies
- Multipart form data support with automatic file/data field splitting
- Closed TypedDict support (PEP 728) via `--use-closed-typed-dict`
- CLI with `openapi-httpx` command
- Python API via `generate()` and `Config`
