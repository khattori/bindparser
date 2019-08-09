# -*- coding: utf-8 -*-
import pyparsing as pp
import ipaddr


COLON = pp.Literal(':')
DOT = pp.Literal('.')
SLASH = pp.Literal('/')

LCURLY = pp.Literal('{').suppress()
RCURLY = pp.Literal('}').suppress()
SEMICOLON = pp.Literal(';').suppress()

QUOTED_STRING = pp.quotedString.addParseAction(pp.removeQuotes)
KEYWORD = pp.Word(pp.alphanums + '-' + '_')
NUMS = pp.Word(pp.nums).setParseAction(lambda toks: int(toks[0]))
INCLUDE = pp.CaselessKeyword('include')

IPv4Field = pp.Word(pp.nums, max=3)
IPv6Field = pp.Word(pp.nums + 'abcdefABCDEF', max=4)
IPv4Prefix = pp.Optional(SLASH + pp.Word(pp.nums, max=2))
IPv6Prefix = pp.Optional(SLASH + pp.Word(pp.nums, max=3))
IPv4Addr = IPv4Field + pp.Optional(DOT + IPv4Field) * 3
IPv6Addr = pp.Combine(
    ((IPv6Field + COLON) * 7 + IPv6Field) ^
    (IPv6Field + COLON + (pp.Optional(IPv6Field + COLON)) * 6 + COLON) ^
    (IPv6Field + COLON + (pp.Optional(IPv6Field + COLON)) * 5 + COLON + IPv6Field) ^
    (IPv6Field + COLON + (pp.Optional(IPv6Field + COLON)) * 4 + COLON + IPv6Field + pp.Optional(COLON + IPv6Field)) ^
    (IPv6Field + COLON + (pp.Optional(IPv6Field + COLON)) * 3 + COLON + IPv6Field + pp.Optional(COLON + IPv6Field) * 2) ^
    (IPv6Field + COLON + (pp.Optional(IPv6Field + COLON)) * 2 + COLON + IPv6Field + pp.Optional(COLON + IPv6Field) * 3) ^
    (IPv6Field + COLON + (pp.Optional(IPv6Field + COLON)) + COLON + IPv6Field + pp.Optional(COLON + IPv6Field) * 4) ^
    (IPv6Field + COLON + COLON + IPv6Field + pp.Optional(COLON + IPv6Field) * 5) ^
    (COLON + COLON + IPv6Field + pp.Optional(COLON + IPv6Field) * 6) ^
    (COLON + COLON)
)

IPAddr = pp.Combine((IPv4Addr + IPv4Prefix) ^ (IPv6Addr + IPv6Prefix)).setParseAction(lambda toks: toAddr(toks[0]))


def toAddr(tok):
    try:
        return ipaddr.IPAddress(tok)
    except:
        return ipaddr.IPNetwork(tok)

#
# named.conf の構文
# -----------------
#
# <syntax> ::= <statement-list>
#
# <statement-list> ::= ( <statement> ';' )*
# <statement> ::= <statement-type> <statement-name>? <statement-class>? '{' <option-list> '}'
#               | 'include' <file-name>
# <statement-type> ::= KEYWORD
# <statement-name> ::= QUOTED_STRING
# <statement-class> ::= KEYWORD
#
# <option-list> ::= ( <option> ';' )*
# <option> ::= KEYWORD <atomic-value>* <value>
#
# <value> ::= <atomic-value> | <complex-value>
#
# <atomic-value> ::= IPADDR | QUOTED_STRING | NUMS | KEYWORD
# <atomic-value-list> ::= ( <atomic-value> ';' )*
#
# <complex-value> ::= '{' <atomic-value-list> | <option-list> '}'
#
def grammar_named_conf():
    option = pp.Forward()
    option_list = pp.ZeroOrMore(option + SEMICOLON)

    atomic_value = NUMS ^ IPAddr ^ QUOTED_STRING ^ KEYWORD
    atomic_value_list = pp.ZeroOrMore(atomic_value + SEMICOLON)
    complex_value = LCURLY + (atomic_value_list ^ option_list) + RCURLY

    option << pp.Group(KEYWORD + pp.Group((pp.OneOrMore(atomic_value) ^ (pp.ZeroOrMore(atomic_value) + complex_value))))
    option_list = pp.Dict(pp.ZeroOrMore(option + SEMICOLON))

    include_statement = pp.Group(INCLUDE + QUOTED_STRING)
    other_statement = pp.Group(KEYWORD + pp.Group(pp.Optional(QUOTED_STRING) + pp.Optional(KEYWORD) + LCURLY + (atomic_value_list ^ option_list) + RCURLY))
    statement = include_statement ^ other_statement
    statement_list = pp.ZeroOrMore(statement + SEMICOLON)

    config = statement_list
    return config.ignore(pp.cppStyleComment ^ pp.pythonStyleComment)


def parse_named_conf(config):
    parser = grammar_named_conf()
    return parser.parseString(config, parseAll=True)


if __name__ == '__main__':
    import sys
    conf_text = '''
logging {
#        channel default_debug {
#                file "data/named.run";
#                severity dynamic;
#        };
#        category lame-servers { null; };
};
'''
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
        with open(file_name) as f:
            conf_text = f.read()
    ret = parse_named_conf(conf_text)
    print ret
