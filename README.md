# bindparser
Parser for named.conf and zone files


# How to test
$ unit2

# How to use

<<<<<<< HEAD
import bindparser as bp
=======
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
>>>>>>> b854ca69d7b3ea4283e9dad5d652ad0157070734
