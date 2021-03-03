#!/usr/bin/env python3
#
# Copyright (c) 2017-2020 Linutronix GmbH
#
# SPDX-License-Identifier: MIT

import libconf
import codecs

import logging
import os
import os.path
import shutil
import hashlib
from subprocess import Popen, PIPE

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from tempfile import TemporaryDirectory

import struct


def getuncompressedsize(filename):
    with open(filename, 'rb') as f:
        f.seek(-4, 2)
        return struct.unpack('I', f.read(4))[0]


def getsha256(filename):

    m = hashlib.sha256()

    with open(filename, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            m.update(data)
    return m.hexdigest()


def find_and_link_file(entry, libdirs):

    fname = entry.filename
    for d in libdirs:
        dname = os.path.join(d, fname)
        if os.path.exists(dname):
            try:
                os.symlink(dname, fname)
            except FileExistsError:
                pass
            return dname


def handle_image(i, opt):
    if 'filename' not in i:
        return

    file_iv = find_and_link_file(i, opt.libdirs)

    sha256 = getsha256(i.filename)
    i['sha256'] = sha256

    if 'volume' in i and 'compressed' in i and (
       i.compressed is True or i.compressed == "zlib"):

        if 'encrypted' in i:
            logging.warning("""The decompressed-size cannot be calculated
                               for preencrypted volumes.""")
        else:
            unc_size = getuncompressedsize(file_iv)
            if 'properties' not in i:
                i['properties'] = {}
            i['properties']['decompressed-size'] = str(unc_size)


def handle_script(i, opt):
    if 'filename' not in i:
        return

    find_and_link_file(i, opt.libdirs)

    sha256 = getsha256(i.filename)
    i['sha256'] = sha256


def find_key(key, d):
    if isinstance(d, dict):
        if key in d:
            for i in d[key]:
                yield i
        for k in d.values():
            for x in find_key(key, k):
                yield x


def main():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter,
                            description='''Generate (signed) swu-update file,
                                           based on information from a
                                           template sw-description.''')
    parser.add_argument("template", metavar="TEMPLATE",
                        help="sw-description template (sw-decription.in)")
    parser.add_argument("--debug", action="store_true", dest="debug",
                        default=False,
                        help="Enable various features for debugging")
    parser.add_argument("-k", "--key", dest="key",
                        help="""pkcs11 uri or file name of the key used for
                                signing the update""")
    parser.add_argument("-o", "--output", dest="output",
                        default="firmware.swu",
                        help="filename of the resulting update file")
    parser.add_argument("-C", "--chdir", dest="chdir",
                        help="""directory where the sw-update cpio archive is
                                built""")
    parser.add_argument("-L", "--libdir", dest="libdirs", action="append",
                        default=['.'],
                        help="""add path where files (e.g. images and scripts)
                                are searched""")

    opt = parser.parse_args()

    # make all paths absolute
    swdescription_in = os.path.abspath(opt.template)
    if opt.key:
        keyfile = os.path.abspath(opt.key)
    opt.output = os.path.abspath(opt.output)
    opt.libdirs = [os.path.abspath(p) for p in opt.libdirs]

    if not opt.chdir:
        temp = TemporaryDirectory()
        opt.chdir = temp.name

    os.chdir(opt.chdir)

    fp = codecs.open(swdescription_in, 'r', 'utf-8')
    cc = libconf.load(fp, filename=swdescription_in)

    for i in find_key('images', cc.software):
        handle_image(i, opt)

    for i in find_key('scripts', cc.software):
        handle_script(i, opt)

    for i in find_key('files', cc.software):
        handle_script(i, opt)

    fp = codecs.open('sw-description', 'w', 'utf-8')
    libconf.dump(cc, fp)
    fp.close()

    files = ['sw-description']
    if opt.key:
        if os.path.isfile(keyfile):
            logging.warning("""Please consider providing a pkcs11 uri instead
                               of a key file.""")
            sign_cmd = 'openssl dgst -sha256 \
                                     -sign "%s" sw-description \
                                     > sw-description.sig' % keyfile
        else:
            sign_cmd = 'openssl dgst -sha256 \
                                     -engine pkcs11 \
                                     -keyform engine \
                                     -sign "%s" sw-description \
                                     > sw-description.sig' % opt.key

        # Preventing the malloc check works around Debian bug #923333
        if os.system('MALLOC_CHECK_=0 ' + sign_cmd) != 0:
            print('failed to sign sw-description')
        files.append('sw-description.sig')

    for i in find_key('images', cc.software):
        if 'filename' in i:
            files.append(i.filename)

    for i in find_key('scripts', cc.software):
        if 'filename' in i:
            files.append(i.filename)

    for i in find_key('files', cc.software):
        if 'filename' in i:
            files.append(i.filename)

    swfp = open(opt.output, 'wb')
    cpio_cmd = 'paxcpio'
    cpio_opt = '-L'
    if not shutil.which(cpio_cmd):
        cpio_cmd = 'cpio'
        cpio_opt = '--dereference'
    cpio = Popen([cpio_cmd, '-ov', '-H', 'crc', cpio_opt],
                 stdin=PIPE, stdout=swfp)

    files_for_cpio = []
    for i in files:
        if i not in files_for_cpio:
            files_for_cpio.append(i)

    for n in files_for_cpio:
        if cpio_cmd == 'cpio' and os.path.getsize(n) > (2 << 30):
            logging.warning('''%s is greater than 2GiB. %s will have a bad
                               checksum with GNU cpio. Install paxcpio or
                               configure SWUpdate with DISABLE_CPIO_CRC.''',
                            n, opt.output)
        cpio.stdin.write(bytes(n+'\n', 'utf-8'))

    cpio.stdin.close()
    cpio.wait()

    swfp.close()

    print('finished')


if __name__ == "__main__":
    main()
