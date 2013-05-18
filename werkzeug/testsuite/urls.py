# -*- coding: utf-8 -*-
"""
    werkzeug.testsuite.urls
    ~~~~~~~~~~~~~~~~~~~~~~~

    URL helper tests.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import unittest
import six
from six import StringIO, next

from werkzeug.testsuite import WerkzeugTestCase

from werkzeug.datastructures import OrderedMultiDict
from werkzeug import urls


class URLsTestCase(WerkzeugTestCase):

    def test_quoting(self):
        assert urls.url_quote(u'\xf6\xe4\xfc') == '%C3%B6%C3%A4%C3%BC'
        assert urls.url_unquote(urls.url_quote(u'#%="\xf6')) == u'#%="\xf6'
        assert urls.url_quote_plus('foo bar') == 'foo+bar'
        assert urls.url_unquote_plus('foo+bar') == 'foo bar'
        self.assertEqual(urls.url_encode({b'a': None, b'b': b'foo bar'}), u'b=foo+bar')
        assert urls.url_encode({u'a': None, u'b': u'foo bar'}) == u'b=foo+bar'
        assert urls.url_fix(u'http://de.wikipedia.org/wiki/Elf (Begriffsklärung)') == \
               b'http://de.wikipedia.org/wiki/Elf%20%28Begriffskl%C3%A4rung%29'

    def test_url_decoding(self):
        x = urls.url_decode(b'foo=42&bar=23&uni=H%C3%A4nsel')
        assert x[b'foo'] == u'42'
        assert x[b'bar'] == u'23'
        assert x[b'uni'] == u'Hänsel'

        x = urls.url_decode(b'foo=42;bar=23;uni=H%C3%A4nsel', separator=b';')
        assert x[b'foo'] == u'42'
        assert x[b'bar'] == u'23'
        assert x[b'uni'] == u'Hänsel'

        x = urls.url_decode(b'%C3%9Ch=H%C3%A4nsel', decode_keys=True)
        assert x[u'Üh'] == u'Hänsel'

    def test_streamed_url_decoding(self):
        item1 = u'a' * 100000
        item2 = u'b' * 400
        string = u'a=%s&b=%s&c=%s' % (item1, item2, item2)
        gen = urls.url_decode_stream(StringIO(string), limit=len(string),
                                     return_iterator=True)
        self.assert_equal(next(gen), (b'a', item1))
        self.assert_equal(next(gen), (b'b', item2))
        self.assert_equal(next(gen), (b'c', item2))
        self.assert_raises(StopIteration, lambda: next(gen))

    def test_url_encoding(self):
        assert urls.url_encode({'foo': 'bar 45'}) == u'foo=bar+45'
        d = {'foo': 1, 'bar': 23, 'blah': u'Hänsel'}
        assert urls.url_encode(d, sort=True) == u'bar=23&blah=H%C3%A4nsel&foo=1'
        assert urls.url_encode(d, sort=True, separator=u';') == u'bar=23;blah=H%C3%A4nsel;foo=1'

    def test_sorted_url_encode(self):
        assert urls.url_encode({u"a": 42, u"b": 23, 1: 1, 2: 2}, sort=True) == u'1=1&2=2&a=42&b=23'
        assert urls.url_encode({u'A': 1, u'a': 2, u'B': 3, 'b': 4}, sort=True,
                          key=lambda x: x[0].lower() + x[0]) == u'A=1&a=2&B=3&b=4'

    def test_streamed_url_encoding(self):
        out = StringIO()
        urls.url_encode_stream({'foo': 'bar 45'}, out)
        self.assert_equal(out.getvalue(), 'foo=bar+45')

        d = {'foo': 1, 'bar': 23, 'blah': u'Hänsel'}
        out = StringIO()
        urls.url_encode_stream(d, out, sort=True)
        self.assert_equal(out.getvalue(), 'bar=23&blah=H%C3%A4nsel&foo=1')
        out = StringIO()
        urls.url_encode_stream(d, out, sort=True, separator=';')
        self.assert_equal(out.getvalue(), 'bar=23;blah=H%C3%A4nsel;foo=1')

        gen = urls.url_encode_stream(d, sort=True)
        self.assert_equal(next(gen), 'bar=23')
        self.assert_equal(next(gen), 'blah=H%C3%A4nsel')
        self.assert_equal(next(gen), 'foo=1')
        self.assert_raises(StopIteration, lambda: next(gen))

    def test_url_fixing(self):
        x = urls.url_fix(u'http://de.wikipedia.org/wiki/Elf (Begriffskl\xe4rung)')
        self.assert_line_equal(x, b'http://de.wikipedia.org/wiki/Elf%20%28Begriffskl%C3%A4rung%29')

    def test_url_fixing_qs(self):
        x = urls.url_fix(b'http://example.com/?foo=%2f%2f')
        self.assert_line_equal(x, b'http://example.com/?foo=%2f%2f')

        x = urls.url_fix(b'http://acronyms.thefreedictionary.com/Algebraic+Methods+of+Solving+the+Schr%C3%B6dinger+Equation')
        self.assertEqual(x, b'http://acronyms.thefreedictionary.com/Algebraic+Methods+of+Solving+the+Schr%C3%B6dinger+Equation')
        

    def test_iri_support(self):
        self.assert_raises(UnicodeError, urls.uri_to_iri, u'http://föö.com/')
        self.assert_raises(UnicodeError, urls.iri_to_uri, u'http://föö.com/'.encode('utf-8'))  # XXX
        assert urls.uri_to_iri(b'http://xn--n3h.net/') == u'http://\u2603.net/'
        assert urls.uri_to_iri(b'http://%C3%BCser:p%C3%A4ssword@xn--n3h.net/p%C3%A5th') == \
            u'http://\xfcser:p\xe4ssword@\u2603.net/p\xe5th'
        assert urls.iri_to_uri(u'http://☃.net/') == b'http://xn--n3h.net/'
        assert urls.iri_to_uri(u'http://üser:pässword@☃.net/påth') == \
            b'http://%C3%BCser:p%C3%A4ssword@xn--n3h.net/p%C3%A5th'

        assert urls.uri_to_iri(b'http://test.com/%3Fmeh?foo=%26%2F') == \
            u'http://test.com/%3Fmeh?foo=%26%2F'

        # this should work as well, might break on 2.4 because of a broken
        # idna codec
        assert urls.uri_to_iri(b'/foo') == u'/foo'
        assert urls.iri_to_uri(u'/foo') == b'/foo'

    def test_ordered_multidict_encoding(self):
        d = OrderedMultiDict()
        d.add('foo', 1)
        d.add('foo', 2)
        d.add('foo', 3)
        d.add('bar', 0)
        d.add('foo', 4)
        self.assertEqual(urls.url_encode(d), u'foo=1&foo=2&foo=3&bar=0&foo=4')

    def test_href(self):
        x = urls.Href(u'http://www.example.com/')
        assert x(u'foo') == u'http://www.example.com/foo'
        assert x.foo(u'bar') == u'http://www.example.com/foo/bar'
        assert x.foo(u'bar', x=42) == u'http://www.example.com/foo/bar?x=42'
        assert x.foo(u'bar', class_=42) == u'http://www.example.com/foo/bar?class=42'
        assert x.foo(u'bar', {u'class': 42}) == u'http://www.example.com/foo/bar?class=42'
        self.assert_raises(AttributeError, lambda: x.__blah__)

        x = urls.Href(u'blah')
        assert x.foo(u'bar') == u'blah/foo/bar'

        self.assert_raises(TypeError, x.foo, {u"foo": 23}, x=42)

        x = urls.Href(u'')
        assert x(u'foo') == u'foo'

    def test_href_url_join(self):
        x = urls.Href(u'test')
        self.assert_line_equal(x(u'foo:bar'), u'test/foo:bar')
        self.assert_line_equal(x(u'http://example.com/'), u'test/http://example.com/')
        self.assert_line_equal(x.a(), u'test/a')

    if 0:
        # stdlib bug? :(
        def test_href_past_root(self):
            base_href = urls.Href('http://www.blagga.com/1/2/3')
            assert base_href('../foo') == 'http://www.blagga.com/1/2/foo'
            assert base_href('../../foo') == 'http://www.blagga.com/1/foo'
            assert base_href('../../../foo') == 'http://www.blagga.com/foo'
            assert base_href('../../../../foo') == 'http://www.blagga.com/foo'
            assert base_href('../../../../../foo') == 'http://www.blagga.com/foo'
            assert base_href('../../../../../../foo') == 'http://www.blagga.com/foo'

    def test_url_unquote_plus_unicode(self):
        # was broken in 0.6
        assert urls.url_unquote_plus(u'\x6d') == u'\x6d'
        assert type(urls.url_unquote_plus(u'\x6d')) is six.text_type

    def test_quoting_of_local_urls(self):
        rv = urls.iri_to_uri(u'/foo\x8f')
        assert rv == b'/foo%C2%8F'
        assert type(rv) is six.binary_type


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(URLsTestCase))
    return suite
