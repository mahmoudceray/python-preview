# 🔍 مراجعة شاملة لمشروع Python Preview Extension

## نظرة عامة
هذا المشروع هو إضافة VSCode لمعاينة تنفيذ كود Python بشكل مرئي (Python Tutor-style visualization). يتكون من:
1. **TypeScript Extension** (`src/`) — الإضافة الخلفية لـ VSCode
2. **Preview Frontend** (`preview-src/`) — واجهة الويب المضمنة (pytutor.ts + webpack)
3. **Python Backend** (`pythonFiles/pydev/`) — محرك التنفيذ والتتبع (pg_logger)

---

## ❌ الأخطاء والمشاكل المكتشفة

### 🔴 مشكلة حرجة #1: بروتوكول `writeString` غير متوافق مع Python

| الجانب | التطبيق الحالي | المطلوب |
|--------|---------------|---------|
| **TypeScript** `writeString` | يكتب `int64(length) + raw_bytes` فقط | يجب كتابة `prefix_byte + int64(length) + bytes` |
| **Python** `read_string` | يقرأ `int64(length) + raw_bytes` | — |

**المشكلة:** دالة `writeString` في [socketStream.ts](file:///I:/Github/python-preview/src/common/net/socket/socketStream.ts#L40-L46) **لا تكتب byte البادئة** (`U`/`A`/`N`)، بينما دالة `write_string` في Python [util.py](file:///I:/Github/python-preview/pythonFiles/pydev/util.py#L50-L65) **تكتب byte البادئة**.

هذا يعني أن البيانات المرسلة من TypeScript → Python ستُقرأ بشكل صحيح (لأن `read_string` في Python لا تتوقع بادئة). لكن البيانات المرسلة من Python → TypeScript ستُقرأ بشكل صحيح أيضاً (لأن `readString` في TypeScript تتوقع بادئة).

**البروتوكول في الواقع متناسق بالتصميم** — لكنه هش جداً ويحتاج توثيق.

> [!NOTE]
> بعد المراجعة الدقيقة، البروتوكول يعمل بشكل صحيح:
> - TS→Python: `writeString` يكتب `int64(len) + bytes` → Python `read_string` يقرأ `int64(len) + bytes` ✅
> - Python→TS: `write_string` يكتب `prefix + int64(len) + bytes` → TS `readString` يقرأ `prefix + int64(len) + bytes` ✅

---

### 🔴 مشكلة حرجة #2: `exec_script_str` — خطأ في ترتيب المعاملات

```diff
# في السطر 1387 من pg_logger.py (exec_script_str):
- logger = PGLogger(options['cumulative_mode'], options['heap_primitives'], options['show_only_outputs'], finalizer_func,
-                   crazy_mode=py_crazy_mode)
+ logger = PGLogger(options['cumulative_mode'], options['heap_primitives'], options['show_only_outputs'], MAX_EXECUTED_LINES, finalizer_func,
+                   crazy_mode=py_crazy_mode)
```

**التوقيع الصحيح لـ `PGLogger.__init__`** (سطر 356):
```python
def __init__(self, cumulative_mode, heap_primitives, show_only_outputs, max_executed_lines, finalizer_func, ...)
```

في `exec_script_str` يتم تمرير `finalizer_func` في مكان `max_executed_lines`! هذا سيسبب خطأ إذا تم استخدام `exec_script_str` (لكن المشروع يستخدم `exec_script_str_local` فقط).

> [!WARNING]
> دالة `exec_script_str` معطلة بسبب خطأ في ترتيب المعاملات — `finalizer_func` يُمرر حيث يُتوقع `max_executed_lines`.

---

### 🔴 مشكلة حرجة #3: تحذير `return` في `finally` (Python 3.14)

```
pg_logger.py:1430: SyntaxWarning: 'return' in a 'finally' block
  return logger.finalize()
```

في [pg_logger.py:1425-1430](file:///I:/Github/python-preview/pythonFiles/pydev/pg_logger.py#L1425-L1430):
```python
try:
    logger._runscript(script_str)
except bdb.BdbQuit:
    pass
finally:
    return logger.finalize()  # ⚠️ return في finally block
```

> [!CAUTION]
> هذا النمط خطير: `return` في `finally` يبتلع أي استثناء لم يُعالج. في Python 3.14+ يُنتج تحذيرًا، وقد يصبح خطأ في إصدارات مستقبلية.

---

### 🟡 مشكلة متوسطة #4: خطأ في `handleInComingData` — فقدان حالة `_statusRead`

في [pythonProcess.ts:92-117](file:///I:/Github/python-preview/src/debugger/pythonProcess.ts#L92-L117):

```typescript
public handleInComingData(buffer: Buffer) {
    this._stream.append(buffer);

    if (!this._guidRead) {
        this._stream.rollBackTransaction();  // ⚠️ لا يوجد beginTransaction قبلها!
        this._stream.readString();
        // ...
    }

    if (!this._statusRead) {
        this._stream.beginTransaction();
        this._stream.readInt32();
        // ...
        this._pidRead = true;  // ⚠️ خطأ! يجب أن يكون this._statusRead = true
        this._stream.endTransaction();
    }
    // ...
}
```

**مشكلتان هنا:**
1. **`rollBackTransaction()` بدون `beginTransaction()`** في معالجة `_guidRead` — هذا يعمل بدون أخطاء لكنه نمط غير صحيح
2. **`this._pidRead = true` بدلاً من `this._statusRead = true`** — هذا يسبب حلقة لانهائية في قراءة الحالة!

---

### 🟡 مشكلة متوسطة #5: Content Security Policy قديم

في [previewContentProvider.ts:24](file:///I:/Github/python-preview/src/features/previewContentProvider.ts#L24):

```html
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; 
  img-src vscode-webview-resource:; 
  media-src vscode-webview-resource:; 
  script-src 'nonce-${nonce}'; 
  style-src vscode-webview-resource: 'unsafe-inline'; 
  font-src vscode-webview-resource: https: http: https: data:;">
```

**المشكلة:** النظام القديم `vscode-webview-resource:` تم استبداله في VS Code الحديث بـ `https://*.vscode-cdn.net` والـ `Webview.asWebviewUri()` API.

> [!IMPORTANT]
> CSP يستخدم `vscode-webview-resource:` scheme القديم. في VS Code ≥1.60 يجب استخدام `webview.cspSource` بدلاً منه.

---

### 🟡 مشكلة متوسطة #6: `extensionResourcePath` يستخدم scheme قديم

في [previewContentProvider.ts:222-226](file:///I:/Github/python-preview/src/features/previewContentProvider.ts#L222-L226):

```typescript
private extensionResourcePath(assetFile: string): string {
    return vscode.Uri.file(this._context.asAbsolutePath(path.join('assets', assetFile)))
        .with({ scheme: 'vscode-webview-resource' })
        .toString();
}
```

**يجب استخدام `webview.asWebviewUri()`** بدلاً من تعيين scheme يدوياً. هذا هو السبب الرئيسي لفشل تحميل CSS وJS في الـ webview.

---

### 🟡 مشكلة متوسطة #7: `fixHref` يستخدم scheme قديم

في [previewContentProvider.ts:37-57](file:///I:/Github/python-preview/src/features/previewContentProvider.ts#L37-L57) — نفس المشكلة.

---

### 🟡 مشكلة متوسطة #8: علامة اقتباس مفقودة في HTML

في [previewContentProvider.ts:206](file:///I:/Github/python-preview/src/features/previewContentProvider.ts#L206):

```typescript
return `<link rel="stylesheet" class="code-user-style" data-source="${style.replace(/"/g, '&quot;')} href="${this.fixHref(resource, style)}" type="text/css" media="screen">`;
```

**مفقود `"`** بعد `data-source` attribute value:
```diff
- data-source="${style.replace(/"/g, '&quot;')} href=
+ data-source="${style.replace(/"/g, '&quot;')}" href=
```

---

### 🟢 مشكلة بسيطة #9: `read_bytes` في Python لا يتعامل مع قطع الاتصال

في [util.py:17-24](file:///I:/Github/python-preview/pythonFiles/pydev/util.py#L17-L24):

```python
def read_bytes(conn, count):
    b = b''
    while len(b) < count:
        received_data = conn.recv(count - len(b))
        if received_data is None:
            break
        b += received_data
    return b
```

**المشكلة:** `socket.recv()` لا ترجع `None` أبداً — ترجع `b''` (بايتات فارغة) عند قطع الاتصال. الفحص يجب أن يكون:
```python
if not received_data:  # بدلاً من received_data is None
    break
```

---

### 🟢 مشكلة بسيطة #10: تحذير `SyntaxWarning` في `exec_script_str`

نفس مشكلة `return` في `finally` في السطر 1402:
```python
try:
    logger._runscript(script_str)
except bdb.BdbQuit:
    pass
finally:
    logger.finalize()  # هنا لا يوجد return، لكن النتيجة ضائعة
```

---

### 🟢 مشكلة بسيطة #11: `assets/` لا يحتوي على CSS

مجلد `assets/` يحتوي فقط على `index.js`. ملفات CSS المطلوبة:
- `jquery-ui.min.css`
- `pytutor.common.css`  
- `pytutor.theme.css`

هذه الملفات **مفقودة** من مجلد `assets/`. يبدو أنها يجب أن تُنسخ من `preview-src/lib/` أو تُنشأ أثناء عملية البناء.

> [!CAUTION]
> ملفات CSS الأساسية مفقودة من مجلد `assets/`! هذا سيمنع الـ webview من العرض بشكل صحيح.

---

### 🟢 مشكلة بسيطة #12: `webview.asWebviewUri()` غير مستخدم

`provideTextDocumentContent` لا يستقبل `webview` كمعامل، مما يمنع استخدام الـ API الحديث `webview.asWebviewUri()`.

---

## 📋 خطة الإصلاح

### المرحلة 1: إصلاحات حرجة (لتشغيل البرنامج)

| # | الإصلاح | الملف | الأولوية |
|---|---------|------|---------|
| 1 | إصلاح `handleInComingData`: `_statusRead = true` بدلاً من `_pidRead = true` | `pythonProcess.ts` | 🔴 |
| 2 | إصلاح `return` في `finally` block في `exec_script_str_local` | `pg_logger.py` | 🔴 |
| 3 | إصلاح `read_bytes` للتعامل مع قطع الاتصال | `util.py` | 🔴 |
| 4 | إضافة ملفات CSS المفقودة إلى مجلد `assets/` | Build process | 🔴 |
| 5 | تحديث `extensionResourcePath` لاستخدام `webview.asWebviewUri()` | `previewContentProvider.ts` | 🔴 |
| 6 | إصلاح علامة الاقتباس المفقودة في `getCustomStyles` | `previewContentProvider.ts` | 🔴 |

### المرحلة 2: تحسينات الاستقرار

| # | الإصلاح | الملف | الأولوية |
|---|---------|------|---------|
| 7 | تمرير `webview` إلى `provideTextDocumentContent` | `previewContentProvider.ts` + `preview.ts` | 🟡 |
| 8 | تحديث CSP لاستخدام `webview.cspSource` | `previewContentProvider.ts` | 🟡 |
| 9 | إصلاح `handleInComingData`: إضافة `beginTransaction()` قبل `rollBackTransaction()` | `pythonProcess.ts` | 🟡 |
| 10 | إصلاح `exec_script_str` — ترتيب معاملات `PGLogger` | `pg_logger.py` | 🟡 |

### المرحلة 3: تحسينات الجودة

| # | الإصلاح | الملف | الأولوية |
|---|---------|------|---------|
| 11 | إزالة `vscode-webview-resource:` scheme من جميع الأماكن | Multiple files | 🟢 |
| 12 | تحسين معالجة الأخطاء في `debugger.py` | `debugger.py` | 🟢 |
| 13 | إعادة بناء `preview-src` (webpack) | `preview-src/` | 🟢 |

---

## هل تريد المتابعة بتنفيذ خطة الإصلاح؟
