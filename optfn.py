from optparse import OptionParser, make_option
import sys
import inspect
import re
import collections

single_char_prefix_re = re.compile('^[a-zA-Z0-9]_')

ERROR_RETURN_CODE = object()

class ErrorCollectingOptionParser(OptionParser):
    def __init__(self, *args, **kwargs):
        self._errors = []
        self._custom_names = {}
        # can't use super() because OptionParser is an old style class
        OptionParser.__init__(self, *args, **kwargs)
    
    def parse_args(self, argv):
        options, args = OptionParser.parse_args(self, argv)
        
        for k,v in options.__dict__.items():
            if k in self._custom_names:
                options.__dict__[self._custom_names[k]] = v
                del options.__dict__[k]
        
        return options, args

    def error(self, msg):
        self._errors.append(msg)

def func_to_optionparser(func):
    if sys.version_info[0] == 3:
        args, varargs, varkw, defaultvals, _, _, _ = inspect.getfullargspec(func)
    else:
        args, varargs, varwk, defaultvals = inspect.getargspec(func)

    defaultvals = defaultvals or ()
    options = zip(args[-len(defaultvals):], defaultvals)
    required_args = args[:-len(defaultvals)] if defaultvals else args[:]
    
    # Build the OptionParser:
    opt = ErrorCollectingOptionParser(usage=func.__doc__)
    
    helpdict = getattr(func, 'optfn_arghelp', {})
    
    # Add the options, automatically detecting their -short and --long names
    shortnames = set(['h'])
    
    for funcname, example in options:
        name = funcname
        
        if single_char_prefix_re.match(name):
            # They either explicitly set the short with x_blah...
            short = name[0]
            name = name[2:]
            opt._custom_names[name] = funcname
        else:
            # Or we pick the first letter from the name not already in use:
            for short in name:
                if short not in shortnames:
                    break
        
        shortnames.add(short)
        short_name = '-%s' % short
        long_name = '--%s' % name.replace('_', '-')
        
        if example in (True, False, bool):
            action = 'store_true'
        else:
            action = 'store'
        
        opt.add_option(make_option(
            short_name, long_name, action=action, dest=name, default=example,
            help = helpdict.get(funcname, '')
        ))

    return len(required_args), varargs != None, opt

def resolve_args(func, argv, **special_pipes):
    num_required_args, has_varargs, parser = func_to_optionparser(func)
    options, args = parser.parse_args(argv)

    # Do we have correct number af required args?
    if num_required_args > len(args) or (num_required_args < len(args) and not has_varargs):
        if not hasattr(func, 'optfn_notstrict'):
            num_required_args_str = "%s or more" % num_required_args if has_varargs else num_required_args
            parser._errors.append('Required %s arguments, got %d' % (num_required_args_str, len(args)))
    
        # Ensure there are enough arguments even if some are missing
        args += [None] * (num_required_args - len(args))
    
    # Special case for stdin/stdout/stderr
    for pipe_name, pipe_value in special_pipes.items():
        if pipe_name in options.__dict__:
            setattr(options, pipe_name, pipe_value)
    
    return args, options.__dict__, parser._errors

def run(func, argv=None, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
    argv = argv or sys.argv[1:]
    include_func_name_in_errors = False
    
    # Handle multiple functions
    if isinstance(func, (tuple, list)):
        funcs = dict([(fn.__name__, fn) for fn in func])

        try:
            func_name = argv.pop(0)
        except IndexError:
            func_name = None
        
        if func_name not in funcs:
            sorted_names = sorted(fn.__name__ for fn in func)
            quoted_names = ["'%s'" % name for name in sorted_names]
            s = ', '.join(quoted_names[:-1])

            if len(quoted_names) > 1:
                s += ' or %s' % quoted_names[-1]
            
            stderr.write("Unknown command: try %s\n" % s)
            return ERROR_RETURN_CODE
        
        func = funcs[func_name]
        include_func_name_in_errors = True

    if isinstance(func, collections.Callable):
        args, kwargs, errors = resolve_args(func, argv, stdin=stdin, stdout=stdout, stderr=stderr)
    else:
        raise TypeError('func is not callable')
    
    # Run the function or return an error if there were argument resolution
    # errors
    if not errors:
        return func(*args, **kwargs)
    else:
        if include_func_name_in_errors:
            stderr.write('%s: ' % func.__name__)

        stderr.write("%s\n" % '\n'.join(errors))
        return ERROR_RETURN_CODE

# Decorators
def notstrict(fn):
    fn.optfn_notstrict = True
    return fn

def arghelp(name, help):
    def inner(fn):
        d = getattr(fn, 'optfn_arghelp', {})
        d[name] = help
        setattr(fn, 'optfn_arghelp', d)
        return fn
    return inner
