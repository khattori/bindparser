# -*- coding: utf-8 -*-
import unittest2
from ipaddr import IPv4Network, IPv4Address
from bindparser import (
    parse_conf_string,
    parse_conf_file,
    parse_zone_string,
    parse_zone_file
)


class TestConfParser(unittest2.TestCase):
    def test_empty(self):
        ret = parse_conf_string('')
        self.assertEqual(ret, [])

    def test_include(self):
        conf_text = '''
include "test.zone";
include "test2.zone";
'''
        ret = parse_conf_string(conf_text)
        self.assertEqual(ret, [{'statement': 'include', 'value': 'test.zone'}, {'statement': 'include', 'value': 'test2.zone'}])

    def test_controls(self):
        conf_text = '''
controls {
      inet 127.0.0.1 allow { localhost; } keys { rndckey; };
};
''' 
        ret = parse_conf_string(conf_text)
        self.assertEqual(ret, [{'value': [('inet', IPv4Address('127.0.0.1'), 'allow', ['localhost'], 'keys', ['rndckey'])], 'statement': 'controls'}])

    def test_key(self):
        conf_text = '''
key "test.key" {
    algrithm hmac-md5;
    secret "secret-key";
};
'''
        ret = parse_conf_string(conf_text)
        self.assertEqual(ret, [{'statement': 'key', 'name': 'test.key', 'value': [('algrithm', 'hmac-md5'), ('secret', 'secret-key')]}])

    def test_zone(self):
        conf_text = '''
zone "." IN {
	type hint;
	file "named.ca";
};
'''
        ret = parse_conf_string(conf_text)
        self.assertEqual(ret, [{'statement': 'zone', 'name': '.', 'value': [('type', 'hint'), ('file', 'named.ca')], 'class': 'IN'}])
        conf_text = 'zone "example.com" IN { type master; file "example.com.zone"; allow-transfer { 192.168.0.2; }; };'
        ret = parse_conf_string(conf_text)
        self.assertEqual(ret, [{'value': [('type', 'master'), ('file', 'example.com.zone'), ('allow-transfer', [IPv4Address('192.168.0.2')])], 'name': 'example.com', 'statement': 'zone', 'class': 'IN'}])

    def test_logging(self):
        conf_text = '''
logging {
    category lame-servers { null; };
    category "default" { null; };
};
'''
        ret = parse_conf_string(conf_text)
        self.assertEqual(ret, [{'value': [('category', 'lame-servers', ['null']), ('category', 'default', ['null'])], 'statement': 'logging'}])

    def test_channel(self):
        conf_text = '''

//syslogデーモンに出力する
channel "default_syslog" {
   syslog daemon;
   severity info;
};

//named.runへ出力する
channel "default_debug" {
   file "named.run";
   severity dynamic;
};

//標準エラーに出力する
channel "default_stderr" {
   stderr;
   severity info;
};

//ログを出力しない
channel "null" {
   null;
};
'''
        ret = parse_conf_string(conf_text)
        self.assertEqual(ret, [
                {'value': [('syslog', 'daemon'), ('severity', 'info')], 'name': 'default_syslog', 'statement': 'channel'},
                {'value': [('file', 'named.run'), ('severity', 'dynamic')], 'name': 'default_debug', 'statement': 'channel'},
                {'value': ['stderr', ('severity', 'info')], 'name': 'default_stderr', 'statement': 'channel'},
                {'value': ['null'], 'name': 'null', 'statement': 'channel'}])

    def test_acl(self):
        conf_text = '''
acl black-hats {
   10.0.2.0/24;
   ! 192.168.0.0/24;
   any;
};

acl red-hats {
   10.0.1.0/24;
};
'''
        ret = parse_conf_string(conf_text)
        self.assertEqual(ret, [{'statement': 'acl', 'name': 'black-hats', 'value': [IPv4Network('10.0.2.0/24'), ('!', IPv4Network('192.168.0.0/24')), 'any']},
                               {'statement': 'acl', 'name': 'red-hats', 'value': [IPv4Network('10.0.1.0/24')]}])

    def test_view(self):
        conf_text = '''
view "internal" {
        match-clients   { localnet; };
        recursion yes;

        zone "." {
             type hint;
             file "named.ca";
        };

        zone "localhost" {
             type master;
             file "localhost.zone";
        };

        zone "0.0.127.in-addr.arpa"{
             type master;
             file "0.0.127.in-addr.arpa.zone";
        };

        zone "in-kororo.jp"{
             type master;
             file "in-kororo.jp.zone";
        };

        zone "50.16.172.in-addr.arpa" {
             type master;
             file "0.50.16.172.in-addr.arpa.zone";
        };


        zone "51.16.172.in-addr.arpa" {
             type master;
             file "0.51.16.172.in-addr.arpa.zone";
        };
};
view "external" {
        match-clients   { any; };
        recursion no;

        zone "kororo.jp"{
             type master;
             file "ex-kororo.jp.zone";
             allow-transfer {
                      localnet;
                      203.141.128.33;
                      195.20.105.149;
             };
        };

        zone "218.117.219.in-addr.arpa"{
             type master;
             file "218.117.219.in-addr.arpa.zone";
             allow-transfer {
                      localnet;
                      203.141.128.33;
                      195.20.105.149;
             };
        };
};
'''
        ret = parse_conf_string(conf_text)
        self.assertEqual(ret, [{'value': [('match-clients', ['localnet']),
                                          ('recursion', 'yes'),
                                          ('zone', '.', [('type', 'hint'), ('file', 'named.ca')]),
                                          ('zone', 'localhost', [('type', 'master'), ('file', 'localhost.zone')]),
                                          ('zone', '0.0.127.in-addr.arpa', [('type', 'master'), ('file', '0.0.127.in-addr.arpa.zone')]),
                                          ('zone', 'in-kororo.jp', [('type', 'master'), ('file', 'in-kororo.jp.zone')]),
                                          ('zone', '50.16.172.in-addr.arpa', [('type', 'master'), ('file', '0.50.16.172.in-addr.arpa.zone')]),
                                          ('zone', '51.16.172.in-addr.arpa', [('type', 'master'), ('file', '0.51.16.172.in-addr.arpa.zone')])],
                                'name': 'internal', 'statement': 'view'},
                               {'value': [('match-clients', ['any']),
                                          ('recursion', 'no'),
                                          ('zone', 'kororo.jp', [('type', 'master'),
                                                                 ('file', 'ex-kororo.jp.zone'),
                                                                 ('allow-transfer', ['localnet', IPv4Address('203.141.128.33'), IPv4Address('195.20.105.149')])]),
                                          ('zone', '218.117.219.in-addr.arpa', [('type', 'master'),
                                                                                ('file', '218.117.219.in-addr.arpa.zone'),
                                                                                ('allow-transfer', ['localnet', IPv4Address('203.141.128.33'), IPv4Address('195.20.105.149')])])],
                                'name': 'external', 'statement': 'view'}])

class TestZoneParser(unittest2.TestCase):
    pass


if __name__ == '__main__':
    unittest2.main()
