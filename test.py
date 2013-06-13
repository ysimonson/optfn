import unittest
import optfunc
from StringIO import StringIO

class FakeStdin(object):
    def read(self):
        return "hello"

class FakeStdout(object):
    def __init__(self):
        self.written = ""

    def write(self, w):
        self.written += w

class TestOptFunc(unittest.TestCase):
    def test_three_positional_args(self):
        def func(one, two, three):
            return "foo"
        
        # Should only have the -h help option
        num_required_args, has_varargs, parser = optfunc.func_to_optionparser(func)
        self.assertEqual(len(parser.option_list), 1)
        self.assertEqual(str(parser.option_list[0]), '-h/--help')
        
        # Should have three required args
        self.assertEqual(num_required_args, 3)
        self.assertEqual(has_varargs, False)
        
        # Running it with the wrong number of arguments should cause an error
        for argv in (['one'], ['one', 'two'], ['one', 'two', 'three', 'four']):
            e = StringIO()
            res = optfunc.run(func, argv, stderr=e)
            self.assert_('Required 3 arguments' in e.getvalue(), e.getvalue())
            self.assertEqual(res, optfunc.ERROR_RETURN_CODE)
        
        # Running it with the right number of arguments should be fine
        e = StringIO()
        res = optfunc.run(func, ['one', 'two', 'three'], stderr=e)
        self.assertEqual(e.getvalue(), '')
        self.assertEqual(res, "foo")

    def test_varargs(self):
        def func(one, two, three, *varargs):
            return "foo", varargs
        
        # Should only have the -h help option
        num_required_args, has_varargs, parser = optfunc.func_to_optionparser(func)
        self.assertEqual(len(parser.option_list), 1)
        self.assertEqual(str(parser.option_list[0]), '-h/--help')
        
        # Should have three required args
        self.assertEqual(num_required_args, 3)
        self.assertEqual(has_varargs, True)
        
        # Running it with the wrong number of arguments should cause an error
        for argv in (['one'], ['one', 'two']):
            e = StringIO()
            res = optfunc.run(func, argv, stderr=e)
            self.assert_('Required 3 or more arguments' in e.getvalue(), e.getvalue())
            self.assertEqual(res, optfunc.ERROR_RETURN_CODE)
        
        # Running it with the right number of arguments should be fine - no varargs
        e = StringIO()
        res = optfunc.run(func, ['one', 'two', 'three'], stderr=e)
        self.assertEqual(e.getvalue(), '')
        self.assertEqual(res, ("foo", ()))

        # Running it with the right number of arguments should be fine - with varargs
        e = StringIO()
        res = optfunc.run(func, ['one', 'two', 'three', 'four', 'five'], stderr=e)
        self.assertEqual(e.getvalue(), '')
        self.assertEqual(res, ("foo", ("four", "five")))
    
    def test_one_arg_one_option(self):
        def func(one, option=''):
            return (one, option)
        
        # Should have -o option as well as -h option
        num_required_args, has_varargs, parser = optfunc.func_to_optionparser(func)
        self.assertEqual(len(parser.option_list), 2)
        strs = [str(o) for o in parser.option_list]
        self.assert_('-h/--help' in strs)
        self.assert_('-o/--option' in strs)
        
        # Should have one required arg
        self.assertEqual(num_required_args, 1)
        self.assertEqual(has_varargs, False)
        
        # Should execute
        res = optfunc.run(func, ['the-required', '-o', 'the-option'])
        self.assertEqual(res, ("the-required", "the-option"))
        
        # Option should be optional
        res = optfunc.run(func, ['required2'])
        self.assertEqual(res, ("required2", ""))
    
    def test_options_are_correctly_named(self):
        def func1(one, option='', verbose=False):
            pass
        
        num_required_args, has_varargs, parser = optfunc.func_to_optionparser(func1)
        strs = [str(o) for o in parser.option_list]
        self.assertEqual(strs, ['-h/--help', '-o/--option', '-v/--verbose'])
    
    def test_option_with_hyphens(self):
        def func2(option_with_hyphens=True):
            pass
        
        num_required_args, has_varargs, parser = optfunc.func_to_optionparser(func2)
        strs = [str(o) for o in parser.option_list]
        self.assertEqual(strs, ['-h/--help', '-o/--option-with-hyphens'])
    
    def test_options_with_same_initial_use_next_letter(self):
        def func1(one, version='', verbose=False):
            pass
        
        num_required_args, has_varargs, parser = optfunc.func_to_optionparser(func1)
        strs = [str(o) for o in parser.option_list]
        self.assertEqual(strs, ['-h/--help', '-v/--version', '-e/--verbose'])

        def func2(one, host=''):
            pass
        
        num_required_args, has_varargs, parser = optfunc.func_to_optionparser(func2)
        strs = [str(o) for o in parser.option_list]
        self.assertEqual(strs, ['-h/--help', '-o/--host'])
    
    def test_short_option_can_be_named_explicitly(self):
        def func1(one, option='', q_verbose=False):
            pass
        
        num_required_args, has_varargs, parser = optfunc.func_to_optionparser(func1)
        strs = [str(o) for o in parser.option_list]
        self.assertEqual(strs, ['-h/--help', '-o/--option', '-q/--verbose'])

        e = StringIO()
        optfunc.run(func1, ['one', '-q'], stderr=e)
        self.assertEqual(e.getvalue().strip(), '')
    
    def test_notstrict(self):
        "@notstrict tells optfunc to tolerate missing required arguments"
        def strict_func(one):
            pass
        
        e = StringIO()
        optfunc.run(strict_func, [], stderr=e)
        self.assertEqual(e.getvalue().strip(), 'Required 1 arguments, got 0')
        
        @optfunc.notstrict
        def notstrict_func(one):
            pass
        
        e = StringIO()
        optfunc.run(notstrict_func, [], stderr=e)
        self.assertEqual(e.getvalue().strip(), '')
    
    def test_arghelp(self):
        "@arghelp('foo', 'help about foo') sets help text for parameters"
        @optfunc.arghelp('foo', 'help about foo')
        def foo(foo = False):
            pass
        
        num_required_args, has_varargs, parser = optfunc.func_to_optionparser(foo)
        opt = parser.option_list[1]
        self.assertEqual(str(opt), '-f/--foo')
        self.assertEqual(opt.help, 'help about foo')
    
    def test_multiple_invalid_subcommand(self):
        "With multiple subcommands, invalid first arg should raise an error"
        def one(arg):
            pass
        def two(arg):
            pass
        def three(arg):
            pass
        
        # Invalid first argument should raise an error
        e = StringIO()
        res = optfunc.run([one, two], ['three'], stderr=e)
        self.assertEqual(res, optfunc.ERROR_RETURN_CODE)
        self.assertEqual(e.getvalue().strip(), "Unknown command: try 'one' or 'two'")

        e = StringIO()
        res = optfunc.run([one, two, three], ['four'], stderr=e)
        self.assertEqual(res, optfunc.ERROR_RETURN_CODE)
        self.assertEqual(e.getvalue().strip(), "Unknown command: try 'one', 'three' or 'two'")
        
        # No argument at all should raise an error
        e = StringIO()
        res = optfunc.run([one, two, three], [], stderr=e)
        self.assertEqual(res, optfunc.ERROR_RETURN_CODE)
        self.assertEqual(e.getvalue().strip(), "Unknown command: try 'one', 'three' or 'two'")
    
    def test_multiple_valid_subcommand_invalid_argument(self):
        "Subcommands with invalid arguments should report as such"
        def one(arg):
            pass
        
        def two(arg):
            pass

        e = StringIO()
        res = optfunc.run([one, two], ['one'], stderr=e)
        self.assertEqual(res, optfunc.ERROR_RETURN_CODE)
        self.assertEqual(e.getvalue().strip(), 'one: Required 1 arguments, got 0')
    
    def test_multiple_valid_subcommand_valid_argument(self):
        "Subcommands with valid arguments should execute as expected"
        def one(arg):
            return "one", arg
        
        def two(arg):
            return "two", arg

        e = StringIO()
        res = optfunc.run([one, two], ['two', 'arg!'], stderr=e)
        self.assertEqual(e.getvalue().strip(), '')
        self.assertEqual(res, ('two', 'arg!'))
    
    def test_stdin_special_argument(self):
        def func(stdin=None):
            return stdin.read()
        
        res = optfunc.run(func, stdin=FakeStdin())
        self.assertEqual(res, "hello")
    
    def test_stdout_special_argument(self):
        def upper(stdin=None, stdout=None):
            stdout.write(stdin.read().upper())
        
        stdout = FakeStdout()
        optfunc.run(upper, stdin=FakeStdin(), stdout=stdout)
        self.assertEqual(stdout.written, 'HELLO')
    
    def test_stderr_special_argument(self):
        def bad_upper(stderr):
            stderr.write('an error')

        def good_upper(stderr=None):
            stderr.write('an error')
        
        stderr = FakeStdout()
        optfunc.run(bad_upper, stderr=stderr)
        self.assertEqual(stderr.written.strip(), 'Required 1 arguments, got 0')

        stderr = FakeStdout()
        optfunc.run(good_upper, stderr=stderr)
        self.assertEqual(stderr.written, 'an error')

    def test_return_arguments(self):
        "Checks that return values of functions are proxied back by run()"

        def one():
            return "one called"
        
        def two():
            return "two called"

        e = StringIO()
        res = optfunc.run([one, two], ['one'], stderr=e)
        self.assertEqual(e.getvalue().strip(), "")
        self.assertEqual(res, "one called")

        e = StringIO()
        res = optfunc.run([one, two], ['three'], stderr=e)
        self.assertEqual(e.getvalue().strip(), "Unknown command: try 'one' or 'two'")
        self.assertEqual(res, optfunc.ERROR_RETURN_CODE)

if __name__ == '__main__':
    unittest.main()
