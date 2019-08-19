# bindparser
Parser for named.conf and zone files


# How to test
$ unit2

# How to use

```
import bindparser as bp
config_text = '''
zone "." IN {
        type hint;
        file "named.ca";
};
'''
bp.parse_config_string(config_text)
```
