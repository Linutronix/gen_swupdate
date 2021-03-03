===============
GEN_SWUPDATE(1)
===============

NAME
====
gen_swupdate - SWU file generator

SYNOPSIS
========
gen_swupdate.py [options] [sw-description.in]

OPTIONS
=======
-h, --help
  show the help message and exit
--debug
  Enable various features for debugging
-k KEY, --key=KEY
  pkcs11 uri or file name of the key used for signing the update
-o OUTPUT, --output=OUTPUT
  filename of the resulting update file
-C CHDIR, --chdir=CHDIR
  directory where the sw-update cpio archive is built
-L LIBDIRS, --libdir=LIBDIRS
  add path where files (e.g. images and scripts) are searched

DESCRIPTION
===========
gen_swupdate is a tool to manage the creation of SWU files, which is the
file format of SWUpdate. SWU files are cpio archives with a meta file that
is called sw-description by default, followed by any other files that,
e.g., can be block or UBIFS images, scripts, bootloader environments, etc.
An overview is available at
https://sbabic.github.io/swupdate/swupdate.html#single-image-delivery
and in-depth documentation on the meta file with many available attributes
at https://sbabic.github.io/swupdate/sw-description.html

Depending on the SWUpdate configuration, several tools are needed in
addition to a cpio implementation to create an SWU file. Especially,
enabling cryptographic hashes or signatures on the included files involves
a non-trivial order of tools like sha256sum or openssl, and adding their
output to the sw-description which is too error-prone to do manually.
After all, sw-description has a tree structure (libconfig or JSON format)
and can become quite complex, especially when a redundant update is to be
implemented with SWUpdate.

SWUpdate does not provide any tooling to create an SWU file, which is why
gen_swupdate was created. Its basic idea is to have a sw-description.in
template with the constant information (e.g., included filenames) of a
sw-description that is processed and the non-constant information (e.g.,
cryptographic hashes, signatures) is filled in to complete the
sw-description. From that and the file list, a complete SWU file is packed
with cpio.

Feature List
------------
The following features are included in gen_swupdate (only a tiny subset of
the overall attribute set):

* implemented with Python and calls to cpio and openssl
* libconfig format
* SHA256 hashes for all included files
* extraction of the decompressed-size of zlib-compressed UBI volumes
* optional: plain RSA signatures for all included files
* using PKCS#11 dongles for signatures

BUGS
====
GNU cpio has a bug (see Debian bug #962188) that makes it
write the wrong CPIO checksum for files greater than 2 GiB.
SWUpdate verifies the checksum and fails for such files.

gen_swupdate uses the paxcpio tool to create the CPIO by default
and falls back to GNU cpio. paxcpio seems to be the only other
common implementation that supports creating the crc format.

SEE ALSO
========
swupdate(1),
openssl(1),
paxcpio(1),
cpio(1)
