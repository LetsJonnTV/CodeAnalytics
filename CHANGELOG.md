# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-01-20

### Added
- Initial release of Code Analytics Tool
- Multi-language syntax highlighting (20+ languages)
- Basic code statistics (lines, characters, words, functions, classes)
- Security analyzer detecting SQL injection, command injection, hardcoded secrets, XSS
- Performance analyzer for inefficient patterns and memory issues
- Quality analyzer with scoring system (A-F grades)
- Code formatting support for multiple languages (Python, JavaScript, TypeScript, HTML, CSS, JSON, etc.)
- External formatter integration (black, prettier, clang-format, gofmt, rustfmt)
- Built-in formatters as fallback
- Modern dark theme UI with ttkbootstrap
- Code structure tree view
- Clickable issues with line navigation
- Search functionality with regex support
- Recent files history
- Export analysis results to HTML
- Customizable settings (theme, font, auto-analyze)
- Keyboard shortcuts for common actions

### Security
- Security vulnerability detection for common patterns
- Warning system for potentially dangerous code

[Unreleased]: https://github.com/username/CodeAnalytics/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/username/CodeAnalytics/releases/tag/v1.0.0
