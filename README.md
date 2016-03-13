OnlyPGPlz
=========
This software is a watchdog that checks your email looking for newly undread and unsigned message. Once one gets found, it reply automatically to the authro of the email saying that you only use PGP for this email account. It's purpose is to inform who write you that you accept only PGP emails, and the second one is of course educate people on the usage of these technology. 


To install:
-----------
download package, unzip, and run:

    python setup.py install

Usage:
--------
To use OnlyPGPlz in the current directory type:

    python OnlyPGPplz.py email@something.com

You can set your favorite log location, and set other parameters in the source.
After your password will be asked, and the sfotware will daemonize.

To kill it, use kill -9 :3
