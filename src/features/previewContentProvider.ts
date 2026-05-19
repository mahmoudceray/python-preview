import * as vscode from 'vscode';
import * as path from 'path';
import {Logger} from '../common/logger';
import {PythonPreviewConfiguration, PythonPreviewConfigurationManager} from './previewConfig';

export class PythonContentProvider {
    constructor(private readonly _context: vscode.ExtensionContext,
                private readonly _logger: Logger) {
    }

    public provideTextDocumentContent(pythonDocument: vscode.TextDocument,
                                      webview: vscode.Webview,
                                      previewConfigurationManager: PythonPreviewConfigurationManager,
                                      state?: any): string {
        const sourceUri = pythonDocument.uri;
        const config = previewConfigurationManager.loadAndCacheConfiguration(sourceUri);

        // Content Security Policy
        const nonce = new Date().getTime() + '' + new Date().getMilliseconds();
        const cspSource = webview.cspSource;

        return `<!DOCTYPE html>
                <html>
                <head>
                    <meta http-equiv="Content-Type" content="text/html;charset=UTF-8">
                    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src ${cspSource}; media-src ${cspSource}; script-src 'nonce-${nonce}'; style-src ${cspSource} 'unsafe-inline'; font-src ${cspSource} https: http: data:;">
                    <meta id="vscode-python-preview-data"
                        data-state="${JSON.stringify(state || {}).replace(/"/g, '&quot;')}">
                    ${this.getStyles(webview, sourceUri, nonce, config)}
                    <base href="${webview.asWebviewUri(pythonDocument.uri)}">
                </head>
                <body>
                <div id="pyOutputPane"></div>
                <script async src="${this.extensionResourcePath(webview, 'index.js')}" nonce="${nonce}"></script>
                </body>
                </html>`;
    }

    private fixHref(webview: vscode.Webview, resource: vscode.Uri, href: string): string {
        if (!href) {
            return href;
        }

        const hrefUri = vscode.Uri.parse(href);
        if (['http', 'https'].indexOf(hrefUri.scheme) >= 0) {
            return hrefUri.toString();
        }

        if (path.isAbsolute(href) || hrefUri.scheme === 'file') {
            return webview.asWebviewUri(vscode.Uri.file(href)).toString();
        }

        const root = vscode.workspace.getWorkspaceFolder(resource);
        if (root) {
            return webview.asWebviewUri(vscode.Uri.file(path.join(root.uri.fsPath, href))).toString();
        }

        return webview.asWebviewUri(vscode.Uri.file(path.join(path.dirname(resource.fsPath), href))).toString();
    }

    private getSettingsOverrideStyles(nonce: string, config: PythonPreviewConfiguration): string {
        return `<style nonce="${nonce}" type="text/css">
            body {
                ${config.styleConfig.fontFamily ? `font-family: ${config.styleConfig.fontFamily};` : ''}
                ${isNaN(config.styleConfig.fontSize) ? '' : `font-size: ${config.styleConfig.fontSize}px;`}
            }
            div.ExecutionVisualizer div#langDisplayDiv {
                ${config.styleConfig.langDisplayFF ? `font-family: ${config.styleConfig.langDisplayFF};` : ''}
                ${isNaN(config.styleConfig.langDisplayFS) ? '' : `font-size: ${config.styleConfig.langDisplayFS}px;`}
            }
            div.ExecutionVisualizer table#pyCodeOutput {
                ${config.styleConfig.codeFF ? `font-family: ${config.styleConfig.codeFF};` : ''}
                ${isNaN(config.styleConfig.codeFS) ? '' : `font-size: ${config.styleConfig.codeFS}px;`}
                ${isNaN(config.styleConfig.codeLH) ? '' : `line-height: ${config.styleConfig.codeLH};`}
            }
            div.ExecutionVisualizer div#legendDiv {
                ${config.styleConfig.legendFF ? `font-family: ${config.styleConfig.legendFF};` : ''}
                ${isNaN(config.styleConfig.legendFS) ? '' : `font-size: ${config.styleConfig.legendFS}px;`}
            }
            div.ExecutionVisualizer div#codeFooterDocs {
                ${config.styleConfig.codeFooterDocsFF ? `font-family: ${config.styleConfig.codeFooterDocsFF};` : ''}
                ${isNaN(config.styleConfig.codeFooterDocsFS) ? '' : `font-size: ${config.styleConfig.codeFooterDocsFS}px;`}
            }
            div.ExecutionVisualizer div#progOutputs {
                ${config.styleConfig.pyStdoutFF ? `font-family: ${config.styleConfig.pyStdoutFF};` : ''}
                ${isNaN(config.styleConfig.pyStdoutFs) ? '' : `font-size: ${config.styleConfig.pyStdoutFs}px;`}
            }
            div.ExecutionVisualizer div#printOutputDocs {
                ${config.styleConfig.printOutputDocsFF ? `font-family: ${config.styleConfig.printOutputDocsFF};` : ''}
                ${isNaN(config.styleConfig.printOutputDocsFS) ? '' : `font-size: ${config.styleConfig.printOutputDocsFS}px;`}
            }
            div.ExecutionVisualizer div#langDisplayDiv {
                ${config.styleConfig.langDisplayFF ? `font-family: ${config.styleConfig.langDisplayFF};` : ''}
                ${isNaN(config.styleConfig.langDisplayFS) ? '' : `font-size: ${config.styleConfig.langDisplayFS}px;`}
            }
            div.ExecutionVisualizer div#stackHeader,
            div.ExecutionVisualizer div#heapHeader {
                ${config.styleConfig.stackAndHeapHeaderFF ? `font-family: ${config.styleConfig.stackAndHeapHeaderFF};` : ''}
                ${isNaN(config.styleConfig.stackAndHeapHeaderFS) ? '' : `font-size: ${config.styleConfig.stackAndHeapHeaderFS}px;`}
            }
            div.ExecutionVisualizer div.stackFrame,
            div.ExecutionVisualizer div.zombieStackFrame {
                ${config.styleConfig.stackFrameFF ? `font-family: ${config.styleConfig.stackFrameFF};` : ''}
                ${isNaN(config.styleConfig.stackFrameFS) ? '' : `font-size: ${config.styleConfig.stackFrameFS}px;`}
            }
            div.ExecutionVisualizer div.stackFrameHeader {
                ${config.styleConfig.stackFrameHeaderFF ? `font-family: ${config.styleConfig.stackFrameHeaderFF};` : ''}
                ${isNaN(config.styleConfig.stackFrameHeaderFS) ? '' : `font-size: ${config.styleConfig.stackFrameHeaderFS}px;`}
            }
            div.ExecutionVisualizer div.heapObject {
                ${config.styleConfig.heapObjectFF ? `font-family: ${config.styleConfig.heapObjectFF};` : ''}
                ${isNaN(config.styleConfig.heapObjectFS) ? '' : `font-size: ${config.styleConfig.heapObjectFS}px;`}
            }
            div.ExecutionVisualizer div.typeLabel {
                ${config.styleConfig.typeLabelFF ? `font-family: ${config.styleConfig.typeLabelFF};` : ''}
                ${isNaN(config.styleConfig.typeLabelFS) ? '' : `font-size: ${config.styleConfig.typeLabelFS}px;`}
            }

            body.vscode-light div.ExecutionVisualizer div.highlightedStackFrame circle {
                ${config.styleConfig.light_highlightedArrow_color ? `fill: ${config.styleConfig.light_highlightedArrow_color};` : ''}
            }
            body.vscode-light div.ExecutionVisualizer div.highlightedStackFrame path {
                ${config.styleConfig.light_highlightedArrow_color ? `stroke: ${config.styleConfig.light_highlightedArrow_color};` : ''}
            }
            body.vscode-light div.ExecutionVisualizer div.highlightedStackFrame path[class] {
                ${config.styleConfig.light_highlightedArrow_color ? `stroke: ${config.styleConfig.light_highlightedArrow_color}; fill: ${config.styleConfig.light_highlightedArrow_color};` : ''}
            }
            body.vscode-light div.ExecutionVisualizer div.highlightedStackFrame {
                ${config.styleConfig.light_highlightedStackFrame_bgColor ? `background-color: ${config.styleConfig.light_highlightedStackFrame_bgColor};` : ''}
            }
            body.vscode-light div.ExecutionVisualizer table.listTbl,
            body.vscode-light div.ExecutionVisualizer table.tupleTbl,
            body.vscode-light div.ExecutionVisualizer table.setTbl {
                ${config.styleConfig.light_list_tuple_setTbl_bgColor ? `background-color: ${config.styleConfig.light_list_tuple_setTbl_bgColor};` : ''}
            }
            body.vscode-light div.ExecutionVisualizer table.dictTbl td.dictKey,
            body.vscode-light div.ExecutionVisualizer table.classTbl td.classKey,
            body.vscode-light div.ExecutionVisualizer table.instTbl td.instKey {
                ${config.styleConfig.light_dict_class_instKey_bgColor ? `background-color: ${config.styleConfig.light_dict_class_instKey_bgColor};` : ''}
            }
            body.vscode-light div.ExecutionVisualizer table.dictTbl td.dictVal,
            body.vscode-light div.ExecutionVisualizer table.classTbl td.classVal,
            body.vscode-light div.ExecutionVisualizer table.instTbl td.instVal {
                ${config.styleConfig.light_dict_class_instVal_bgColor ? `background-color: ${config.styleConfig.light_dict_class_instVal_bgColor};` : ''}
            }

            body.vscode-dark div.ExecutionVisualizer div.highlightedStackFrame circle {
                ${config.styleConfig.dark_highlightedArrow_color ? `fill: ${config.styleConfig.dark_highlightedArrow_color};` : ''}
            }
            body.vscode-dark div.ExecutionVisualizer div.highlightedStackFrame path {
                ${config.styleConfig.dark_highlightedArrow_color ? `stroke: ${config.styleConfig.dark_highlightedArrow_color};` : ''}
            }
            body.vscode-dark div.ExecutionVisualizer div.highlightedStackFrame path[class] {
                ${config.styleConfig.dark_highlightedArrow_color ? `stroke: ${config.styleConfig.dark_highlightedArrow_color}; fill: ${config.styleConfig.dark_highlightedArrow_color};` : ''}
            }
            body.vscode-dark div.ExecutionVisualizer div.highlightedStackFrame {
                ${config.styleConfig.dark_highlightedStackFrame_bgColor ? `background-color: ${config.styleConfig.dark_highlightedStackFrame_bgColor};` : ''}
            }
            body.vscode-dark div.ExecutionVisualizer table.listTbl,
            body.vscode-dark div.ExecutionVisualizer table.tupleTbl,
            body.vscode-dark div.ExecutionVisualizer table.setTbl {
                ${config.styleConfig.dark_list_tuple_setTbl_bgColor ? `background-color: ${config.styleConfig.dark_list_tuple_setTbl_bgColor};` : ''}
            }
            body.vscode-dark div.ExecutionVisualizer table.dictTbl td.dictKey,
            body.vscode-dark div.ExecutionVisualizer table.classTbl td.classKey,
            body.vscode-dark div.ExecutionVisualizer table.instTbl td.instKey {
                ${config.styleConfig.dark_dict_class_instKey_bgColor ? `background-color: ${config.styleConfig.dark_dict_class_instKey_bgColor};` : ''}
            }
            body.vscode-dark div.ExecutionVisualizer table.dictTbl td.dictVal,
            body.vscode-dark div.ExecutionVisualizer table.classTbl td.classVal,
            body.vscode-dark div.ExecutionVisualizer table.instTbl td.instVal {
                ${config.styleConfig.dark_dict_class_instVal_bgColor ? `background-color: ${config.styleConfig.dark_dict_class_instVal_bgColor};` : ''}
            }

            body.vscode-high-contrast div.ExecutionVisualizer div.highlightedStackFrame circle {
                ${config.styleConfig.highContrast_highlightedArrow_color ? `fill: ${config.styleConfig.highContrast_highlightedArrow_color};` : ''}
            }
            body.vscode-high-contrast div.ExecutionVisualizer div.highlightedStackFrame path {
                ${config.styleConfig.highContrast_highlightedArrow_color ? `stroke: ${config.styleConfig.highContrast_highlightedArrow_color};` : ''}
            }
            body.vscode-high-contrast div.ExecutionVisualizer div.highlightedStackFrame path[class] {
                ${config.styleConfig.highContrast_highlightedArrow_color ? `stroke: ${config.styleConfig.highContrast_highlightedArrow_color}; fill: ${config.styleConfig.highContrast_highlightedArrow_color};` : ''}
            }
            body.vscode-high-contrast div.ExecutionVisualizer div.highlightedStackFrame {
                ${config.styleConfig.highContrast_highlightedStackFrame_bgColor ? `background-color: ${config.styleConfig.highContrast_highlightedStackFrame_bgColor};` : ''}
            }
            body.vscode-high-contrast div.ExecutionVisualizer table.listTbl,
            body.vscode-high-contrast div.ExecutionVisualizer table.tupleTbl,
            body.vscode-high-contrast div.ExecutionVisualizer table.setTbl {
                ${config.styleConfig.highContrast_list_tuple_setTbl_bgColor ? `background-color: ${config.styleConfig.highContrast_list_tuple_setTbl_bgColor};` : ''}
            }
            body.vscode-high-contrast div.ExecutionVisualizer table.dictTbl td.dictKey,
            body.vscode-high-contrast div.ExecutionVisualizer table.classTbl td.classKey,
            body.vscode-high-contrast div.ExecutionVisualizer table.instTbl td.instKey {
                ${config.styleConfig.highContrast_dict_class_instKey_bgColor ? `background-color: ${config.styleConfig.highContrast_dict_class_instKey_bgColor};` : ''}
            }
            body.vscode-high-contrast div.ExecutionVisualizer table.dictTbl td.dictVal,
            body.vscode-high-contrast div.ExecutionVisualizer table.classTbl td.classVal,
            body.vscode-high-contrast div.ExecutionVisualizer table.instTbl td.instVal {
                ${config.styleConfig.highContrast_dict_class_instVal_bgColor ? `background-color: ${config.styleConfig.highContrast_dict_class_instVal_bgColor};` : ''}
            }
        </style>`;
    }

    private getCustomStyles(webview: vscode.Webview, resource: vscode.Uri, config: PythonPreviewConfiguration): string {
        if (Array.isArray(config.styleConfig.styles)) {
            return config.styleConfig.styles.map(style => {
                return `<link rel="stylesheet" class="code-user-style" data-source="${style.replace(/"/g, '&quot;')}" href="${this.fixHref(webview, resource, style)}" type="text/css" media="screen">`;
            }).join('\n');
        }
        return '';
    }

    private getStyles(webview: vscode.Webview, resource: vscode.Uri, nonce: string, config: PythonPreviewConfiguration): string {
        const baseStyles = ['jquery-ui.min.css', 'pytutor.common.css', 'pytutor.theme.css']
            .map(item => `<link rel="stylesheet" type="text/css" href="${this.extensionResourcePath(webview, item)}">`)
            .join('\n');

        return `${baseStyles}
                ${this.getSettingsOverrideStyles(nonce, config)}
                ${this.getCustomStyles(webview, resource, config)}`;
    }

    private extensionResourcePath(webview: vscode.Webview, assetFile: string): string {
        return webview.asWebviewUri(
            vscode.Uri.file(this._context.asAbsolutePath(path.join('assets', assetFile)))
        ).toString();
    }
}