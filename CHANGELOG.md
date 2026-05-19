# Change Log

## Version 1.0.0

### Major Release - Complete Modernization

#### Python Support
- Full support for Python 3.11, 3.12, and 3.13
- Removed all Python 2 compatibility code from `pythonFiles/pydev/`
- Replaced deprecated `imp.new_module()` with `types.ModuleType()` in `pg_logger.py`
- Replaced deprecated `inspect.getargspec()` with `inspect.getfullargspec()` in `pg_encoder.py`
- Fixed `__builtins__` handling for Python 3 (dict vs module variations)
- Updated string handling in `util.py` to use ASCII encoding directly

#### TypeScript & Build Tools
- Updated TypeScript from 3.x to 5.4 with ES2022 target and strict mode
- Updated Webpack from 4.x to 5.x with modern configuration
- Updated Gulp from 3.x to 4.x with series/parallel syntax
- Replaced TSLint with ESLint (`@typescript-eslint/eslint-plugin` 7.0)
- Updated test runner to `@vscode/test-electron` 2.3.9
- Updated VS Code engine requirement to ^1.85.0

#### Frontend Libraries
- Updated jQuery from 3.0.0 to 3.7.1
- Updated jQuery UI from 1.11.4 to 1.13.2
- Retained jsPlumb 1.3.10 (breaking API changes in newer versions)
- Added TypeScript type definitions for jQuery and jQuery UI

#### Code Quality Improvements
- Fixed all TypeScript strict mode errors across 20+ files
- Added proper null/undefined handling with type unions
- Fixed Deferred type signatures in `helpers.ts`
- Added null checks for `proc.stderr`/`proc.stdout` in `localDebugClient.ts`
- Fixed uninitialized properties with proper initializers
- Replaced `this` aliasing with direct `this` usage
- Changed `{}` types to `unknown` for better type safety
- Auto-fixed ESLint issues: quotes, semicolons, const usage
- Added `global.d.ts` for d3 and jsPlumb declarations

#### Bug Fixes
- Fixed `cumulativeMode` setting invalid error
- Fixed typo: `cumulativeModde` → `cumulativeMode`
- Fixed `valiate` → `validate` in error messages
- Fixed code white-space and codeLineNumber text-align
- Unified scrollbar style
- Fixed `_cachedoutputs` typo → `_cachedOutputs` in `previewManager.ts`

#### Testing
- All 6 unit tests passing
- 10 integration tests covering:
  - Basic variable assignment
  - List operations
  - Function definition and calls
  - Dictionary operations
  - Class definition and instantiation
  - Cumulative mode tracing
  - Trace structure validation
  - Print output capture
  - Error handling
  - Module imports

#### Dependencies Updated
| Package | Old Version | New Version |
|---------|-------------|-------------|
| typescript | ^3.x | ^5.4.0 |
| webpack | ^4.x | ^5.91.0 |
| gulp | ^3.x | ^4.0.2 |
| eslint | N/A (TSLint) | ^8.56.0 |
| @vscode/test-electron | N/A | ^2.3.9 |
| @types/mocha | ^5.x | ^10.0.6 |
| @types/node | ^10.x | ^20.11.0 |
| @types/vscode | ^1.x | ^1.85.0 |
| jquery | 3.0.0 | 3.7.1 |
| jquery-ui | 1.11.4 | 1.13.2 |

## Version 0.0.4
- Fix: Fixed cumulativeMode setting invalid error

## Version 0.0.3
- Fix: Fixed style error.

## Version 0.0.2
- Eliminate unnecessary contents from extension.
- Add third party notices.
- Add settingDemo.gif.

## Version 0.0.1
- Initial release
