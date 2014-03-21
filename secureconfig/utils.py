import os, string
from random import sample, choice

from keyczar import keyczar, keyczart
from keyczar.errors import KeyczarError

KEYCZAR_CREATE = 'create --location=%(loc)s --purpose=crypt'
KEYCZAR_ADDKEY = 'addkey --location=%(loc)s --status=primary'

ACCEPTED_SYMBOLS = '_-)(&^#@!.'

def safe_pwgen(length=32, symbols=ACCEPTED_SYMBOLS):
    '''returns a non-human-readable password of length=length (default 32) and 
        symbols as desired default ACCEPTED_SYMBOLS:  _-)(&^#@!.'''
    chars = string.letters + string.digits + symbols
    return ''.join(choice(chars) for _ in range(length))

def initialize_keys(keyloc, name="Test"):
    _initialize(keyloc, name=name)

def keydir_status(keyloc):
    if os.path.exists(keyloc):
        if not os.path.isdir(keyloc):
            return "Key directory does not exist"
    try:
        test = keyczar.Crypter.Read(keyloc)
    except KeyczarError:
        return "Bad keys or no keys initialized"

    return "OK"
    

def encrypt_file(keyloc, infile, outfile=''):
    enctxt = encrypt(keyloc, open(infile, 'r').read())
    f=open(outfile, 'wb')
    f.write(enctxt)
    f.close()

def decrypt_file(keyloc, infile, outfile=''):
    txt = decrypt(open(infile, 'rb').read())
    if outfile:
        f=open(outfile, 'w')
        f.write(txt)
        f.close()     
        return outfile
    else:
        return txt

def encrypt(keyloc, inp):
    crypter = keyczar.Crypter.Read(keyloc)
    return crypter.Encrypt(inp)

def decrypt(keyloc, inp):
    crypter = keyczar.Crypter.Read(keyloc)
    return crypter.Decrypt(inp)

def _require_dir(keyloc):
    '''Make sure that keyloc is a directory.
    If it does not exist, create it.
    '''
    if os.path.exists(keyloc):
        if not os.path.isdir(keyloc):
            raise ValueError('%s must be a directory' % keyloc)
    else:
        os.makedirs(keyloc, 0700)


def _tool(fmt, **kwds):
    '''Package the call to keyczart.main
    which is awkwardly setup for command-line use without
    organizing the underlying logic for direct function calls.
    '''
    return keyczart.main( (fmt % kwds).split() )

def _initialize(keyloc, **kwds):
    '''Initialize a location
    create it
    add a primary key
    '''
    _require_dir(keyloc)
    steps = [KEYCZAR_CREATE, KEYCZAR_ADDKEY]
    for step in steps:
        _tool(step, loc=keyloc, **kwds)


if __name__=='__main__':
    KEYLOC = 'keys'
    #initialize_keys(KEYLOC)
    encrypt_file('keys', 'sample_plain.txt', 'sample_enc.txt')

