"""Unittest for idlelib.HyperParser"""
import unittest
from test.support import requires
from tkinter import Tk, Text
from idlelib.EditorWindow import EditorWindow
from idlelib.HyperParser import HyperParser

class DummyEditwin:
    def __init__(self, text):
        self.text = text
        self.indentwidth = 8
        self.tabwidth = 8
        self.context_use_ps1 = True
        self.num_context_lines = 50, 500, 1000

    _build_char_in_string_func = EditorWindow._build_char_in_string_func
    is_char_in_string = EditorWindow.is_char_in_string


class HyperParserTest(unittest.TestCase):
    code = (
            '"""This is a module docstring"""\n'
            '# this line is a comment\n'
            'x = "this is a string"\n'
            "y = 'this is also a string'\n"
            'l = [i for i in range(10)]\n'
            'm = [py*py for # comment\n'
            '       py in l]\n'
            'x.__len__\n'
            "z = ((r'asdf')+('a')))\n"
            '[x for x in\n'
            'for = False\n'
            )

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = Tk()
        cls.text = Text(cls.root)
        cls.editwin = DummyEditwin(cls.text)

    @classmethod
    def tearDownClass(cls):
        del cls.text, cls.editwin
        cls.root.destroy()
        del cls.root

    def setUp(self):
        self.text.insert('insert', self.code)

    def tearDown(self):
        self.text.delete('1.0', 'end')
        self.editwin.context_use_ps1 = True

    def get_parser(self, index):
        """
        Return a parser object with index at 'index'
        """
        return HyperParser(self.editwin, index)

    def test_init(self):
        """
        test corner cases in the init method
        """
        with self.assertRaises(ValueError) as ve:
            self.text.tag_add('console', '1.0', '1.end')
            p = self.get_parser('1.5')
        self.assertIn('precedes', str(ve.exception))

        # test without ps1
        self.editwin.context_use_ps1 = False

        # number of lines lesser than 50
        p = self.get_parser('end')
        self.assertEqual(p.rawtext, self.text.get('1.0', 'end'))

        # number of lines greater than 50
        self.text.insert('end', self.text.get('1.0', 'end')*4)
        p = self.get_parser('54.5')

    def test_is_in_string(self):
        get = self.get_parser

        p = get('1.0')
        self.assertFalse(p.is_in_string())
        p = get('1.4')
        self.assertTrue(p.is_in_string())
        p = get('2.3')
        self.assertFalse(p.is_in_string())
        p = get('3.3')
        self.assertFalse(p.is_in_string())
        p = get('3.7')
        self.assertTrue(p.is_in_string())
        p = get('4.6')
        self.assertTrue(p.is_in_string())

    def test_is_in_code(self):
        get = self.get_parser

        p = get('1.0')
        self.assertTrue(p.is_in_code())
        p = get('1.1')
        self.assertFalse(p.is_in_code())
        p = get('2.5')
        self.assertFalse(p.is_in_code())
        p = get('3.4')
        self.assertTrue(p.is_in_code())
        p = get('3.6')
        self.assertFalse(p.is_in_code())
        p = get('4.14')
        self.assertFalse(p.is_in_code())

    def test_get_surrounding_bracket(self):
        get = self.get_parser

        def without_mustclose(parser):
            # a utility function to get surrounding bracket
            # with mustclose=False
            return parser.get_surrounding_brackets(mustclose=False)

        def with_mustclose(parser):
            # a utility function to get surrounding bracket
            # with mustclose=True
            return parser.get_surrounding_brackets(mustclose=True)

        p = get('3.2')
        self.assertIsNone(with_mustclose(p))
        self.assertIsNone(without_mustclose(p))

        p = get('5.6')
        self.assertTupleEqual(without_mustclose(p), ('5.4', '5.25'))
        self.assertTupleEqual(without_mustclose(p), with_mustclose(p))

        p = get('5.23')
        self.assertTupleEqual(without_mustclose(p), ('5.21', '5.24'))
        self.assertTupleEqual(without_mustclose(p), with_mustclose(p))

        p = get('6.15')
        self.assertTupleEqual(without_mustclose(p), ('6.4', '6.end'))
        self.assertIsNone(with_mustclose(p))

        p = get('9.end')
        self.assertIsNone(with_mustclose(p))
        self.assertIsNone(without_mustclose(p))

    def test_get_expression(self):
        get = self.get_parser

        p = get('4.2')
        self.assertEqual(p.get_expression(), 'y ')

        p = get('4.7')
        with self.assertRaises(ValueError) as ve:
            p.get_expression()
        self.assertIn('is inside a code', str(ve.exception))

        p = get('5.25')
        self.assertEqual(p.get_expression(), 'range(10)')

        p = get('6.7')
        self.assertEqual(p.get_expression(), 'py')

        p = get('6.8')
        self.assertEqual(p.get_expression(), '')

        p = get('7.9')
        self.assertEqual(p.get_expression(), 'py')

        p = get('8.end')
        self.assertEqual(p.get_expression(), 'x.__len__')

        p = get('9.13')
        self.assertEqual(p.get_expression(), "r'asdf'")

        p = get('9.17')
        with self.assertRaises(ValueError) as ve:
            p.get_expression()
        self.assertIn('is inside a code', str(ve.exception))

        p = get('10.0')
        self.assertEqual(p.get_expression(), '')

        p = get('11.3')
        self.assertEqual(p.get_expression(), '')

        p = get('11.11')
        self.assertEqual(p.get_expression(), 'False')


if __name__ == '__main__':
    unittest.main(verbosity=2)
