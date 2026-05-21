# Online Python Tutor
# https://github.com/pgbovine/OnlinePythonTutor/
#
# Copyright (C) Philip J. Guo (philip@pgbovine.net)
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


# Given an arbitrary piece of Python data, encode it in such a manner
# that it can be later encoded into JSON.
#   http://json.org/
#
# We use this function to encode run-time traces of data structures
# to send to the front-end.
#
# Format:
#   Primitives:
#   * None, int, float, str, bool - unchanged
#     (json.dumps encodes these fine verbatim, except for inf, -inf, and nan)
#
#   exceptions: float('inf')  -> ['SPECIAL_FLOAT', 'Infinity']
#               float('-inf') -> ['SPECIAL_FLOAT', '-Infinity']
#               float('nan')  -> ['SPECIAL_FLOAT', 'NaN']
#               x == int(x)   -> ['SPECIAL_FLOAT', '%.1f' % x]
#               (this way, 3.0 prints as '3.0' and not as 3, which looks like an int)
#
#   If render_heap_primitives is True, then primitive values are rendered
#   on the heap as ['HEAP_PRIMITIVE', <type name>, <value>]
#
#   (for SPECIAL_FLOAT values, <value> is a list like ['SPECIAL_FLOAT', 'Infinity'])
#
#   added on 2018-06-13:
#   ['IMPORTED_FAUX_PRIMITIVE', <label>] - renders externally imported objects
#                                          like they were primitives, to save
#                                          space and to prevent from having to
#                                          recurse into of them to see internals
#
#   Compound objects:
#   * list     - ['LIST', elt1, elt2, elt3, ..., eltN]
#   * tuple    - ['TUPLE', elt1, elt2, elt3, ..., eltN]
#   * set      - ['SET', elt1, elt2, elt3, ..., eltN]
#   * dict     - ['DICT', [key1, value1], [key2, value2], ..., [keyN, valueN]]
#   * instance - ['INSTANCE', class name, [attr1, value1], [attr2, value2], ..., [attrN, valueN]]
#   * instance with non-trivial __str__ defined - ['INSTANCE_PPRINT', class name, <__str__ value>, [attr1, value1], [attr2, value2], ..., [attrN, valueN]]
#   * class    - ['CLASS', class name, [list of superclass names], [attr1, value1], [attr2, value2], ..., [attrN, valueN]]
#   * function - ['FUNCTION', function name, parent frame ID (for nested functions),
#                 [*OPTIONAL* list of pairs of default argument names/values] ] <-- final optional element added on 2018-06-13
#   * module   - ['module', module name]
#   * other    - [<type name>, string representation of object]
#   * compound object reference - ['REF', target object's unique_id]
#
# the unique_id is derived from id(), which allows us to capture aliasing


# number of significant digits for floats
FLOAT_PRECISION = 4


from collections import defaultdict, deque
import re, types
import sys
import math
import array
classRE = re.compile("<class '(.*)'>")

import inspect


def is_class(dat):
    """Return whether dat is a class."""
    return isinstance(dat, type)


def is_instance(dat):
    """Return whether dat is an instance of a class."""
    return type(dat) not in PRIMITIVE_TYPES and \
           isinstance(type(dat), type) and \
           not isinstance(dat, type)


def get_name(obj):
    """Return the name of an object."""
    return obj.__name__ if hasattr(obj, '__name__') else get_name(type(obj))


PRIMITIVE_TYPES = (int, float, str, bool, type(None))

def encode_primitive(dat):
    t = type(dat)
    if t is float:
        if math.isinf(dat):
            if dat > 0:
                return ['SPECIAL_FLOAT', 'Infinity']
            else:
                return ['SPECIAL_FLOAT', '-Infinity']
        elif math.isnan(dat):
            return ['SPECIAL_FLOAT', 'NaN']
        else:
            # render floats like 3.0 as '3.0' and not as 3
            if dat == int(dat):
                return ['SPECIAL_FLOAT', '%.1f' % dat]
            else:
                return round(dat, FLOAT_PRECISION)
    else:
        # return all other primitives verbatim
        return dat


# grab a line number like ' <line 2>' or ' <line 2b>'
def create_lambda_line_number(codeobj, line_to_lambda_code):
    try:
        lambda_lineno = codeobj.co_firstlineno
        lst = line_to_lambda_code[lambda_lineno]
        ind = lst.index(codeobj)
        lineno_str = str(lambda_lineno)
        return ' <line ' + lineno_str + '>'
    except Exception:
        return ''


# Note that this might BLOAT MEMORY CONSUMPTION since we're holding on
# to every reference ever created by the program without ever releasing
# anything!
class ObjectEncoder:
    def __init__(self, parent):
        self.parent = parent  # should be a PGLogger object

        # Key: canonicalized small ID
        # Value: encoded (compound) heap object
        self.encoded_heap_objects = {}

        self.render_heap_primitives = parent.render_heap_primitives

        self.id_to_small_IDs = {}
        self.cur_small_ID = 1

        # (assumes everything is in one file)
        # Key:   line number
        # Value: list of the code objects of lambdas defined
        #        on that line in the order they were defined
        self.line_to_lambda_code = defaultdict(list)

    def should_hide_var(self, var):
        return self.parent.should_hide_var(var)

    # searches through self.parents.types_to_inline and tries
    # to match the type returned by type(obj).__name__ and
    # also 'class' and 'instance' for classes and instances, respectively
    def should_inline_object_by_type(self, obj):
        # fast-pass optimization -- common case
        if not self.parent.types_to_inline:
            return False

        # copy-pasted from the end of self.encode()
        typ = type(obj)
        typename = typ.__name__

        # pick up built-in functions too:
        if typ in (types.FunctionType, types.MethodType, types.BuiltinFunctionType, types.BuiltinMethodType):
            typename = 'function'

        if not typename:
            return False

        alt_typename = None
        if is_class(obj):
            alt_typename = 'class'
        elif is_instance(obj) and typename != 'function':
            typename = 'instance'
            class_name = None
            if hasattr(obj, '__class__'):
                class_name = get_name(obj.__class__)
            else:
                class_name = get_name(type(obj))
            alt_typename = class_name

        for re_match in self.parent.types_to_inline:
            if re_match(typename):
                return True
            if alt_typename and re_match(alt_typename):
                return True
        return False

    def get_heap(self):
        return self.encoded_heap_objects

    def reset_heap(self):
        # VERY IMPORTANT to reassign to an empty dict rather than just
        # clearing the existing dict, since get_heap() could have been
        # called earlier to return a reference to a previous heap state
        self.encoded_heap_objects = {}

    def set_function_parent_frame_ID(self, ref_obj, enclosing_frame_id):
        assert ref_obj[0] == 'REF'
        func_obj = self.encoded_heap_objects[ref_obj[1]]
        assert func_obj[0] == 'FUNCTION'
        func_obj[-1] = enclosing_frame_id

    # return either a primitive object or an object reference;
    # and as a side effect, update encoded_heap_objects
    def encode(self, dat, get_parent):
        """Encode a data value DAT using the GET_PARENT function for parent ids."""
        # primitive type
        if not self.render_heap_primitives and type(dat) in PRIMITIVE_TYPES:
            return encode_primitive(dat)
        # compound type - return an object reference and update encoded_heap_objects
        else:
            # IMPORTED_FAUX_PRIMITIVE feature added on 2018-06-13:
            is_externally_defined = False  # is dat defined in external (i.e., non-user) code?
            try:
                # some objects don't return anything for getsourcefile() but DO return
                # something legit for getmodule(). e.g., "from io import StringIO"
                # so TRY getmodule *first* and then fall back on getsourcefile
                # since getmodule seems more robust empirically ...
                gsf = inspect.getmodule(dat).__file__
                if not gsf:
                    gsf = inspect.getsourcefile(dat)

                # a hacky heuristic is that if gsf is an absolute path, then it's likely
                # to be some library function and *not* in user-defined code
                #
                # NB: don't use os.path.isabs() since it doesn't work on some
                # python installations (e.g., on my webserver) and also adds a
                # dependency on the os module. just do a simple check:
                #
                # hacky: do other checks for strings that are indicative of files
                # that load user-written code, like 'generate_json_trace.py'
                if gsf and gsf[0] == '/' and 'generate_json_trace.py' not in gsf:
                    is_externally_defined = True
            except (AttributeError, TypeError):
                pass  # fail soft
            my_id = id(dat)

            # if dat is an *real* object instance (and not some special built-in one
            # like ABCMeta, or a py3 function object), then DON'T treat it as
            # externally-defined because a user might be instantiating an *instance*
            # of an imported class in their own code, so we want to show that instance
            # in da visualization - ugh #hacky
            if (is_instance(dat) and
                type(dat) not in (types.FunctionType, types.MethodType, types.BuiltinFunctionType, types.BuiltinMethodType) and
                hasattr(dat, '__class__') and (get_name(dat.__class__) != 'ABCMeta')):
                is_externally_defined = False

            # if this is an externally-defined object (i.e., from an imported
            # module, don't try to recurse into it since we don't want to see
            # the internals of imported objects; just return an
            # IMPORTED_FAUX_PRIMITIVE object and continue along on our way
            if is_externally_defined:
                label = 'object'
                try:
                    label = type(dat).__name__
                    if is_class(dat):
                        label = 'class'
                    elif is_instance(dat):
                        label = 'object'
                except Exception:
                    pass
                return ['IMPORTED_FAUX_PRIMITIVE', 'imported ' + label]  # punt early!

            # next check whether it should be inlined
            if self.should_inline_object_by_type(dat):
                label = 'object'
                try:
                    label = type(dat).__name__
                    if is_class(dat):
                        class_name = get_name(dat)
                        label = class_name + ' class'
                    elif is_instance(dat):
                        class_name = None
                        if hasattr(dat, '__class__'):
                            class_name = get_name(dat.__class__)
                        else:
                            class_name = get_name(type(dat))
                        if class_name:
                            label = class_name + ' instance'
                        else:
                            label = 'instance'
                except Exception:
                    pass
                return ['IMPORTED_FAUX_PRIMITIVE', label + ' (hidden)']  # punt early!

            try:
                my_small_id = self.id_to_small_IDs[my_id]
            except KeyError:
                my_small_id = self.cur_small_ID
                self.id_to_small_IDs[my_id] = self.cur_small_ID
                self.cur_small_ID += 1

            del my_id  # to prevent bugs later in this function

            ret = ['REF', my_small_id]

            # punt early if you've already encoded this object
            if my_small_id in self.encoded_heap_objects:
                return ret

            # major side-effect!
            new_obj = []
            self.encoded_heap_objects[my_small_id] = new_obj

            typ = type(dat)

            if isinstance(dat, list):
                new_obj.append('LIST')
                for e in dat:
                    new_obj.append(self.encode(e, get_parent))
            elif isinstance(dat, tuple):
                new_obj.append('TUPLE')
                for e in dat:
                    new_obj.append(self.encode(e, get_parent))
            elif isinstance(dat, (set, frozenset)):
                new_obj.append('SET')
                for e in dat:
                    new_obj.append(self.encode(e, get_parent))
            elif isinstance(dat, dict):
                new_obj.append('DICT')
                for (k, v) in dat.items():
                    # don't display some built-in locals ...
                    if k not in ('__module__', '__return__', '__locals__'):
                        new_obj.append([self.encode(k, get_parent), self.encode(v, get_parent)])
            elif isinstance(dat, (bytes, bytearray)):
                new_obj.extend(['BYTES', type(dat).__name__, repr(dat)])
            elif isinstance(dat, range):
                new_obj.extend(['RANGE', dat.start, dat.stop, dat.step])
            elif isinstance(dat, complex):
                new_obj.extend(['COMPLEX', self.encode(dat.real, get_parent), self.encode(dat.imag, get_parent)])
            elif isinstance(dat, slice):
                new_obj.extend(['SLICE', dat.start, dat.stop, dat.step])
            elif isinstance(dat, deque):
                new_obj.append('DEQUE')
                for e in dat:
                    new_obj.append(self.encode(e, get_parent))
            elif isinstance(dat, array.array):
                new_obj.append('ARRAY')
                new_obj.append(dat.typecode)
                for e in dat:
                    new_obj.append(self.encode(e, get_parent))
            elif isinstance(dat, (enumerate, zip, map, filter)) or type(dat).__name__ in ('reversed', 'list_reverseiterator', 'tuple_reverseiterator', 'str_reverseiterator'):
                new_obj.extend(['ITERABLE', type(dat).__name__, repr(dat)])
            elif isinstance(dat, types.GeneratorType):
                state = 'suspended'
                if dat.gi_frame is None:
                    state = 'exhausted'
                elif dat.gi_running:
                    state = 'running'
                details = {}
                details['code_name'] = dat.gi_code.co_name
                details['lineno'] = dat.gi_code.co_firstlineno
                if dat.gi_yieldfrom is not None:
                    details['yieldfrom'] = repr(dat.gi_yieldfrom)
                new_obj.append('GENERATOR')
                new_obj.append(state)
                if details:
                    new_obj.append(details)
            elif isinstance(dat, types.CoroutineType):
                state = 'suspended'
                if dat.cr_frame is None:
                    state = 'finished'
                elif dat.cr_running:
                    state = 'running'
                details = {}
                details['code_name'] = dat.cr_code.co_name
                details['lineno'] = dat.cr_code.co_firstlineno
                if dat.cr_await is not None:
                    details['await'] = repr(dat.cr_await)
                new_obj.append('COROUTINE')
                new_obj.append(state)
                if details:
                    new_obj.append(details)
            elif isinstance(dat, types.AsyncGeneratorType):
                state = 'suspended'
                if dat.ag_frame is None:
                    state = 'exhausted'
                elif dat.ag_running:
                    state = 'running'
                details = {}
                details['code_name'] = dat.ag_code.co_name
                details['lineno'] = dat.ag_code.co_firstlineno
                new_obj.append('ASYNC_GENERATOR')
                new_obj.append(state)
                if details:
                    new_obj.append(details)
            elif isinstance(dat, staticmethod):
                wrapped = dat.__func__
                if wrapped:
                    new_obj.append('STATICMETHOD')
                    new_obj.append(self.encode(wrapped, get_parent))
                else:
                    new_obj.extend(['STATICMETHOD', None])
            elif isinstance(dat, classmethod):
                wrapped = dat.__func__
                if wrapped:
                    new_obj.append('CLASSMETHOD')
                    new_obj.append(self.encode(wrapped, get_parent))
                else:
                    new_obj.extend(['CLASSMETHOD', None])
            elif isinstance(dat, property):
                prop_info = {}
                prop_info['name'] = dat.fget.__name__ if dat.fget else '?'
                if dat.fget:
                    prop_info['fget'] = self.encode(dat.fget, get_parent)
                if dat.fset:
                    prop_info['fset'] = self.encode(dat.fset, get_parent)
                if dat.fdel:
                    prop_info['fdel'] = self.encode(dat.fdel, get_parent)
                prop_doc = dat.__doc__
                if prop_doc and prop_doc != prop_info['name']:
                    prop_info['doc'] = prop_doc
                new_obj.append('PROPERTY')
                new_obj.append(prop_info)
            elif isinstance(dat, (types.FunctionType, types.MethodType)):
                argspec = inspect.getfullargspec(dat)

                printed_args = [e for e in argspec.args]

                default_arg_names_and_vals = []
                if argspec.defaults:
                    num_missing_defaults = len(printed_args) - len(argspec.defaults)
                    assert num_missing_defaults >= 0
                    # tricky tricky tricky how default positional arguments work!
                    for i in range(num_missing_defaults, len(printed_args)):
                        default_arg_names_and_vals.append((printed_args[i], self.encode(argspec.defaults[i-num_missing_defaults], get_parent)))

                if argspec.varargs:
                    printed_args.append('*' + argspec.varargs)

                # kwonlyargs come before varkw
                if argspec.kwonlyargs:
                    printed_args.extend(argspec.kwonlyargs)
                    if argspec.kwonlydefaults:
                        # iterate in order of appearance in kwonlyargs
                        for varname in argspec.kwonlyargs:
                            if varname in argspec.kwonlydefaults:
                                val = argspec.kwonlydefaults[varname]
                                default_arg_names_and_vals.append((varname, self.encode(val, get_parent)))
                if argspec.varkw:
                    printed_args.append('**' + argspec.varkw)

                func_name = get_name(dat)

                pretty_name = func_name

                # sometimes might fail for, say, <genexpr>, so just ignore
                # failures for now ...
                try:
                    pretty_name += '(' + ', '.join(printed_args) + ')'
                except TypeError:
                    pass

                # put a line number suffix on lambdas to more uniquely identify
                # them, since they don't have names
                if func_name == '<lambda>':
                    cod = dat.__code__
                    lst = self.line_to_lambda_code[cod.co_firstlineno]
                    if cod not in lst:
                        lst.append(cod)
                    pretty_name += create_lambda_line_number(cod,
                                                             self.line_to_lambda_code)

                encoded_val = ['FUNCTION', pretty_name, None]
                if get_parent:
                    enclosing_frame_id = get_parent(dat)
                    encoded_val[2] = enclosing_frame_id
                new_obj.extend(encoded_val)

                # Build optional details dict (backward-compatible)
                details = {}
                if default_arg_names_and_vals:
                    details['defaults'] = default_arg_names_and_vals

                # Closure info: free variables and their cell values
                if hasattr(dat, '__closure__') and dat.__closure__:
                    freevars = dat.__code__.co_freevars
                    closure_cells = dat.__closure__
                    closure_vars = []
                    for i, cell in enumerate(closure_cells):
                        if i < len(freevars):
                            try:
                                closure_vars.append((freevars[i], self.encode(cell.cell_contents, get_parent)))
                            except ValueError:
                                pass
                    if closure_vars:
                        details['closure'] = closure_vars

                # Code object info
                code = dat.__code__
                details['code'] = {
                    'varnames': list(code.co_varnames),
                    'nlocals': code.co_nlocals,
                    'filename': code.co_filename,
                    'name': code.co_name,
                    'freevars': list(code.co_freevars),
                    'argcount': code.co_argcount,
                    'kwonlyargcount': code.co_kwonlyargcount,
                    'consts': [repr(c) if isinstance(c, (int, float, str, bool, type(None))) else type(c).__name__ for c in code.co_consts[:15]]
                }

                # Globals info (limited to keys for reference)
                try:
                    gkeys = list(dat.__globals__.keys())[:30]
                    details['globals_keys'] = gkeys
                except Exception:
                    pass

                # Decorator info
                if hasattr(dat, '__wrapped__'):
                    details['has_wrapped'] = True

                if details:
                    # Use dict format if any non-defaults info exists, otherwise array for backward compat
                    if len(details) == 1 and 'defaults' in details:
                        new_obj.append(details['defaults'])
                    else:
                        new_obj.append(details)

            elif typ is types.BuiltinFunctionType:
                pretty_name = get_name(dat) + '(...)'
                new_obj.extend(['FUNCTION', pretty_name, None])
            elif is_class(dat) or is_instance(dat):
                self.encode_class_or_instance(dat, new_obj)
            elif typ is types.ModuleType:
                new_obj.extend(['module', dat.__name__])
            elif typ in PRIMITIVE_TYPES:
                assert self.render_heap_primitives
                new_obj.extend(['HEAP_PRIMITIVE', type(dat).__name__, encode_primitive(dat)])
            else:
                typeStr = str(typ)
                m = classRE.match(typeStr)

                assert m, typ

                encoded_dat = str(dat)
                new_obj.extend([m.group(1), encoded_dat])

            return ret

    def encode_class_or_instance(self, dat, new_obj):
        """Encode dat as a class or instance."""
        if is_instance(dat):
            if hasattr(dat, '__class__'):
                # common case ...
                class_name = get_name(dat.__class__)
            else:
                class_name = get_name(type(dat))

            pprint_str = None
            # do you or any of your superclasses have a __str__ field? if so, pretty-print yourself!
            if hasattr(dat, '__str__'):
                try:
                    pprint_str = dat.__str__()

                    # sometimes you'll get 'trivial' pprint_str like: '<__main__.MyObj object at 0x10f465cd0>'
                    # or '<module 'collections' ...'
                    # IGNORE THOSE!!!
                    if pprint_str[0] == '<' and pprint_str[-1] == '>' and (' at ' in pprint_str or pprint_str.startswith('<module')):
                        pprint_str = None
                except Exception:
                    pass

            # TODO: filter for trivial-looking pprint_str like those produced
            # by object.__str__
            if pprint_str:
                new_obj.extend(['INSTANCE_PPRINT', class_name, pprint_str])
            else:
                new_obj.extend(['INSTANCE', class_name])

            # don't traverse inside modules, or else risk EXPLODING the visualization
            if class_name == 'module':
                return
        else:
            # Use full MRO chain instead of just __bases__
            mro_names = [e.__name__ for e in dat.__mro__ if e is not dat and e is not object]
            superclass_names = [e.__name__ for e in dat.__bases__ if e is not object]
            new_obj.extend(['CLASS', get_name(dat), superclass_names])
            new_obj.append(mro_names)

        # traverse inside of its __dict__ to grab attributes
        # (filter out useless-seeming ones, based on anecdotal observation):
        hidden = ('__doc__', '__module__', '__return__', '__dict__',
            '__locals__', '__weakref__', '__qualname__')
        user_attrs = []
        if hasattr(dat, '__dict__'):
            user_attrs = [e for e in dat.__dict__ if e not in hidden]

        # Also include __slots__ attributes for instances
        if is_instance(dat):
            try:
                slots = getattr(type(dat), '__slots__', ())
                if isinstance(slots, str):
                    slots = (slots,)
                for slot in slots:
                    if slot not in hidden and slot not in user_attrs and hasattr(dat, slot):
                        user_attrs.append(slot)
            except Exception:
                pass

        user_attrs.sort()

        for attr in user_attrs:
            if not self.should_hide_var(attr):
                if hasattr(dat, '__dict__') and attr in dat.__dict__:
                    new_obj.append([self.encode(attr, None), self.encode(dat.__dict__[attr], None)])
                else:
                    new_obj.append([self.encode(attr, None), self.encode(getattr(dat, attr), None)])

        # ABC info for classes
        if is_class(dat) and hasattr(dat, '__abstractmethods__') and dat.__abstractmethods__:
            new_obj.append(['__abstractmethods__', list(dat.__abstractmethods__)])

        # Dataclass info
        if is_class(dat) and hasattr(dat, '__dataclass_fields__'):
            fields = list(dat.__dataclass_fields__.keys())
            new_obj.append(['@dataclass fields', fields])

        # fallback: if instance has no user attributes and no pretty-print string, try repr()
        if is_instance(dat) and not pprint_str and not user_attrs:
            try:
                r = repr(dat)
                if not (r[0] == '<' and ' at 0x' in r):
                    new_obj[0] = 'INSTANCE_PPRINT'
                    new_obj.insert(2, r)
            except Exception:
                pass
