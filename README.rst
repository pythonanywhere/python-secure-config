************
secureconfig
************

by Naomi Most (@nthmost)

A simple solution to the often annoying problem of protecting config files.

secureconfig makes keeping your secrets secure on servers and source control 
repositories easy by restricting your choices on the matter, defaulting to 
a "medium-high paranoia" set of operations.

Those choices, specifically::

   Use AES-128 CBC via Fernet (see https://cryptography.io/en/latest/fernet/ )
   Store keys in environment variables, or in files protected by the system.
   Provide an easy way to overwrite sensitive string data left behind by with zeroes.

This library has undergone an overhaul since last version, so if you were using 0.0.2.x,
please read the below carefully so you understand what has changed (A LOT!).

The major philosophical shift was to separate the duties of encryption and data 
structure handling into the CryptKeeper classes and SecureConfig* classes. This means 
that if you just want a consistent way to encrypt/decrypt strings and files that works
across all of your data structures, the CryptKeeper classes will come in handy.

Config styles currently supported::

    ConfigParser (see SecureConfigParser)
    Json (see SecureJson) -- whole-data encryption only.
    serialized dictionaries (see SecureConfig) -- whole-data encryption only.

Please let the maintainer (@nthmost) know if you want to see another type supported.

Purpose
-------

secureconfig is being developed in the context of an open-source-loving,
"information wants to be free" kind of company that also does not wish to 
get totally pwned in a heartbeat when, say, bitbucket has a major security
breach. 

We have a lot of pre-existing code that makes use of ConfigParser ini-style
files and also JSON config files. The best solution for protecting our 
services and sensitive information would be to create a drop-in replacement
for ConfigParser that allows us to keep 99% of the way we interact with
config files, and simply wraps the decryption step.

Of course, once you have decryption handled, you start to want simplified 
ways of encrypting as well.

That's why secureconfig (as of 0.0.3) supports writing new config files.
See "basic usage" sections below to see how you can easily turn a plaintext
value or file into an encrypted value or file (depending on config style).

The CryptKeeper classes can even generate new keys for you.  Just make sure 
you keep track of which keys match with your data; this library will not stop
you from shooting yourself in the foot!

secureconfig also tries to be helpful in keeping stored keys secure. FileCryptKeeper
has "paranoid" mode on by default, which means that it will check to see whether the
key is in a directory protected by your operating system. If not, it will refuse to
run.  (Turn this off using paranoid=False, if you must.)

Finally, secureconfig contains a smattering of deployment utilities found in 
secureconfig.utils.  Feel free to suggest new ones.

This library can be found at https://bitbucket.org/nthmost/python-secureconfig 

Contributions and code/documentation critiques are warmly welcomed.


How secureconfig Works
----------------------

At its core, secureconfig simply subclasses the configuration mechanisms we 
all know and love, and wraps certain operations (read-from-file and/or 
read-and-interpolate) in a decryption layer.

This library bases its operations on Fernet, a cryptography meta-protocol (see
https://cryptography.io) developed to help programmers choose the best possible
defaults for their encryption tasks.

The CryptKeeper classes handle key storage, en/decryption, and key generation.
All SecureConfig* classes receive from_x class instantiation methods to set up
an internal CryptKeeper. 

Table of Methods of key storage - CryptKeeper class - SecureConfig* classmethod:: 

    string -- CryptKeeper -- .from_key(key_string)
    file -- FileCryptKeeper -- .from_file(key_filename)
    environment variable -- EnvCryptKeeper -- .from_env(key_env_name)

All CryptKeeper classes have a default argument of `proactive=True`, which means
that the CryptKeeper instance will try to store a key in that place whether it
currently exists or not.  If this place is not writeable, you'll get your OS's usual
error for an attempted operation.

When proactive=False and locations do not exist, you'll get a KeyError for environment
variables or an OSError for file operations.

If CryptKeeper classes are instantiated without a key argument, they will generate
a key automatically for you. 

Another way to generate a new key is to use the CryptKeeper classmethod `.generate_key()`.

NOTICE:  You can't assign a new key to a CryptKeeper object after it's been created and
have it work. (If that seems like misbehaviour, let me know; it's changeable.)

All of the SecureConfig* classes can be used with or without encryption keys,
although you'll get a SecureConfigException('bad data or no encryption key') if
you try to parse a data structure (such as JSON) out of encrypted text.


SecureConfigParser
------------------

NEW SINCE 0.1.0:

SecureConfigParser is a subclass of the configparser module's ConfigParser class.

The difference is that, when instantiated via one of the standardized cryptkeeper 
classmethods (see above) so that a private key is supplied, SecureConfigParser
detects encrypted entries and decrypts them when demanded (i.e. when .get is used).

So, unlike SecureJson, this class encrypts and decrypts single values rather than
entire files.

All of the usual ConfigParser methods are available.

In addition, you can set new values into the config to be encrypted by supplying
`encrypt=True` as an argument to the .set method. See an example of this below.


.. code-block:: python

    from secureconfig import SecureConfigParser, SecureString

    # starting with an ini file that has unencrypted entries:
    configpath = '/etc/app/config.ini'

    key_env = 'SCP_INI_KEY'

    scfg = SecureConfigParser.from_env('SCP_INI_KEY')
    scfg.read(configpath)

    user = scfg.get('credentials', 'username')
    pass = SecureString(scfg.get('credentials', 'password'))
        
    connection = GetSomeConnection(username, password)

    # SecureString overwrites its string data with zeroes upon garbage collection.
    del(pass)

    # IMPORTANT: supply encrypt=True to encrypt values.
    config.set('credentials', 'password', 'better_password', encrypt=True)
    
    fh=open('/path/to/new_scfp.ini', 'w')
    config.write(fh)
    fh.close()


SecureJson
----------

SecureJson is a very simple wrapper around JSON data. It decrypts whole files
(or whole strings) and can encrypt new configurations as well.

Use one of the cryptkeeper classmethods above to instantiate with a key.

SecureJson will happily process plaintext data as well if no key is supplied.

SecureJson is a subclass of SecureConfig (see below), and as such, as some
ConfigParser-like operations included.


Basic usage (CHANGED SINCE 0.1.0):

.. code-block:: python

    from secureconfig import SecureJson, SecureString

    configpath = '/etc/app/config.json.enc'

    config = SecureJson.from_file('.keys/aes_key', filepath=configpath)

    username = config.get('credentials', 'username')
    password = SecureString(config.get('credentials', 'password'))

    connection = GetSomeConnection(username, password)

    # SecureString overwrites its string data with zeroes upon garbage collection.
    del(password)
    
    # set a new password 
    config.set('credentials', 'password', 'better_password')
    
    fh=open('/path/to/config.json.enc', 'w')
    config.write(fh)
    fh.close()



SecureConfig
------------

WARNING: 

The way SecureConfig reads data back is via literal_eval. This approach may not
be without its concerns, so please do not use this class to work with data you 
do not explicitly trust.

The lowly SecureConfig class's lot in life is to be subclassed by other objects.
But it can still be somewhat useful.

SecureConfig stores data in serialized dictionaries, which are then encrypted
as a whole and stored as an undecipherable blob of information. The data can only
be read and recovered by supplying the private key that it was encrypted with.

SecureConfig provides a .cfg dictionary for raw access.  It also provides many ConfigParser
style interactions (see class docstring), including .get and .set methods.  This works as
long as your data is at least 2-dimensional.  

You can still use SecureConfig with 1-dimensional data (i.e. flat dictionary of key=value
pairs); you just can't use the ConfigParser style interactions. 

Below is demonstrated the non-ConfigParser style of interacting with SecureConfig data.

Basic Usage (CHANGED SINCE 0.1.0):

.. code-block:: python

    from secureconfig import SecureConfig, SecureString

    config = SecureJson.from_file('.keys/aes_key')

    cfg = config.cfg

    username = cfg['username']
    password = SecureString(cfg['password'])

    connection = GetSomeConnection(username, password)

    # password's string data will be overwritten with zeroes when garbage-collected.
    del(password)



Future
------

Planned features include::

- more automated-deployment-oriented utils
- asymmetric key deployments (e.g. RSA public key encryption)


CONTACT
-------

Look for @nthmost on Twitter if you're interested and would like to contribute!
Comments and critiques warmly welcomed.

--Naomi Most, spring 2014.

