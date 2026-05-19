# Python Preview extension for Visual Studio Code

A [Visual Studio Code](https://code.visualstudio.com/) [extension](https://marketplace.visualstudio.com/VSCode) with debugging preview support for the [Python language](https://www.python.org/).

## Version 1.0.0 - Major Release

This release represents a complete modernization of the extension with full Python 3.11-3.13 support, updated dependencies, and improved code quality.

## Features

![Preview](https://raw.githubusercontent.com/dongli0x00/python-preview/master/images/previewDemo.gif)

![Setting](https://raw.githubusercontent.com/dongli0x00/python-preview/master/images/settingDemo.gif)

### What's New in 1.0.0

- **Full Python 3.11-3.13 Support**: Removed all Python 2 compatibility code and fixed Python 3.11+ incompatibilities
- **Modern TypeScript**: Updated to TypeScript 5.4 with strict mode and ES2022 target
- **Updated Build Tools**: Webpack 5, Gulp 4, ESLint replacing deprecated TSLint
- **Updated Frontend Libraries**: jQuery 3.7.1, jQuery UI 1.13.2 (jsPlumb 1.3.10 retained for compatibility)
- **Improved Type Safety**: Fixed all TypeScript strict mode errors across the codebase
- **Code Quality**: ESLint integration with 0 errors, comprehensive test coverage

## Requirements

1. Install Python 3.11, 3.12, or 3.13. Make sure the Python interpreter location is included in your PATH environment variable.
2. It's recommended to install the [Python Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) for Python Intellisense.

## Installation

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "Python Preview"
4. Click Install

## Usage

- Open a Python file
- Click the preview icon in the editor title bar or use the command palette (`Ctrl+Shift+P`) and search for "Python Preview"
- Use keyboard shortcuts:
  - `Shift+Ctrl+V`: Open preview
  - `Ctrl+K V`: Open preview to the side

## Configuration

The extension provides extensive configuration options for customizing the visualization appearance:

### Trace Settings
- `pythonPreview.cumulativeMode`: Show cumulative state (default: true)
- `pythonPreview.maxExecutedLines`: Maximum lines to execute (default: 1000)
- `pythonPreview.allowAllModules`: Allow importing all modules (default: true)

### Display Settings
- `pythonPreview.fontFamily`: Base font family
- `pythonPreview.fontSize`: Base font size (default: 16)
- `pythonPreview.codAndNavWidth`: Code and navigation panel width (default: 510)

### Theme Colors
Customize colors for light, dark, and high contrast themes for:
- Highlighted arrows and stack frames
- List/tuple/set tables
- Dictionary/class/instance keys and values

## Change Log

You can checkout all our changes in our [change log](https://github.com/dongli0x00/python-preview/blob/master/CHANGELOG.md).

## Development

### Build from Source

```bash
# Install dependencies
npm install
cd preview-src && npm install && cd ..

# Compile TypeScript
npm run compile

# Build frontend
cd preview-src && npx webpack --config webpack.prod.js && cd ..

# Run tests
npm test

# Lint
npm run lint
```

### Project Structure

```
python-preview/
├── src/                    # TypeScript extension source
│   ├── commands/           # VS Code commands
│   ├── common/             # Shared utilities
│   ├── debugger/           # Debug client/server implementation
│   ├── features/           # Preview functionality
│   └── test/               # Unit tests
├── preview-src/            # Frontend visualization source
│   ├── lib/                # Frontend libraries (jQuery, jQuery UI, jsPlumb, D3)
│   ├── pytutor.ts          # Main visualization controller
│   └── webpack.*.js        # Webpack configuration
├── pythonFiles/            # Python execution tracing scripts
│   └── pydev/              # Core Python debugging utilities
├── assets/                 # UI assets
└── out/                    # Compiled output
```

## Thanks

Thanks to the following projects which I rely on and obtain a number of fresh new ideas from
- [OnlinePythonTutor](https://github.com/pgbovine/OnlinePythonTutor)
- [vscode-python](https://github.com/Microsoft/vscode-python)
- [markdown-language-features](https://github.com/Microsoft/vscode/tree/master/extensions/markdown-language-features)

Also special thanks to the people that have provided support, testing, etc:
- [JianWei Hong](https://github.com/HongHaiyang)

And finally thanks to the [Python](https://www.python.org/) development team and community and of course the awesome [vscode](https://github.com/Microsoft/vscode/graphs/contributors) team.

## License

[MIT License](LICENSE)
