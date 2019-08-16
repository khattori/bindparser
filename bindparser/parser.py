# -*- coding: utf-8 -*-
import pyparsing as pp
import ipaddr
from decorator import decorator

#
# 変換のための補助関数
#
@decorator
def action(f, toks):
    tok = toks[0]
    return f(tok)


@action
def _to_int(tok):
    return int(tok)


@action
def _to_addr(tok):
    try:
        return ipaddr.IPAddress(tok)
    except:
        return ipaddr.IPNetwork(tok)


@action
def _to_tuple(tok):
    if len(tok) > 1:
        return tuple(tok)
    else:
        return tok


COLON = pp.Literal(':')
DOT = pp.Literal('.')
SLASH = pp.Literal('/')

LCURLY = pp.Literal('{').suppress()
RCURLY = pp.Literal('}').suppress()
SEMICOLON = pp.Literal(';').suppress()

QUOTED_STRING = pp.quotedString.addParseAction(pp.removeQuotes)
KEYWORD = pp.Word(pp.alphanums + '-' + '_')
NUMS = pp.Word(pp.nums).setParseAction(_to_int)
NEGATE = pp.Keyword('!')

# statements
ACL = pp.CaselessKeyword('acl')
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
IPAddr = pp.Combine((IPv4Addr + IPv4Prefix) ^ (IPv6Addr + IPv6Prefix)).setParseAction(_to_addr)

#
# named.conf の構文
# -----------------
#
# <syntax> ::= <statement-list>
#
# <statement-list> ::= ( <statement> ';' )*
# <statement> ::= 'acl' <name> <statement-options>
#               | 'controls' <statement-options>
#               | 'include' QUOTED_STRING
#               | 'key' <name> <statement-options>
#               | 'logging' <statement-options>
#               | 'options' <statement-options>
#               | 'server' IPADDR <statement-options>
#               | 'trusted-keys' <statement-options>
#               | 'view' <name> <statement-options>
#               | 'zone' <name> KEYWORD? <statement-options>
# <statement-options> = '{' <option-list> '}'
# <name> ::= QUOTED_STRING | KEYWORD
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
    atomic_value = NUMS ^ NEGATE ^ IPAddr ^ QUOTED_STRING ^ KEYWORD
    value = pp.Forward()
    element = pp.Group(pp.OneOrMore(value)).setParseAction(_to_tuple)
    element_list = pp.ZeroOrMore(element + SEMICOLON)
    bracketed_value = pp.Group(LCURLY + element_list + RCURLY)
    value << (atomic_value ^ bracketed_value)

    name = QUOTED_STRING ^ KEYWORD
    include_stmt = INCLUDE.setResultsName('statement') + QUOTED_STRING.setResultsName('value')
    acl_stmt = ACL.setResultsName('statement') + name.setResultsName('name') + bracketed_value.setResultsName('value')
    other_stmt = KEYWORD.setResultsName('statement') + pp.Optional(name).setResultsName('name') + pp.Optional(KEYWORD).setResultsName('class') + bracketed_value.setResultsName('value')
    statement = pp.Group(include_stmt ^ acl_stmt ^ other_stmt)
    statement_list = pp.ZeroOrMore(statement + SEMICOLON)

    #
    # 以下はコメントとして無視する
    # - cppスタイルコメント: //, /* */
    # - pythonスタイルコメント: #
    #
    config = statement_list
    return config.ignore(pp.cppStyleComment ^ pp.pythonStyleComment)


def _conv_result(v):
    if isinstance(v, (pp.ParseResults, list)):
        return [_conv_result(x) for x in v]
    if isinstance(v, tuple):
        return tuple(_conv_result(x) for x in v)
    elif isinstance(v, dict):
        return dict((k, _conv_result(v)) for k, v in v.items())
    else:
        return v


def _parse_conf(method, config):
    parser = grammar_named_conf()
    parse_fun = getattr(parser, method)
    return [_conv_result(stmt.asDict()) for stmt in parse_fun(config, parseAll=True)]


def parse_conf_string(conf_text):
    return _parse_conf('parseString', conf_text)


def parse_conf_file(conf_file):
    return _parse_conf('parseFile', conf_file)


def parse_zone_string(zone_text):
    pass


def parse_zone_file(file_or_filename):
    pass
