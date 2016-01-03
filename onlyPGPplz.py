import email
import imaplib
import re
import sys
import smtplib
import getpass
from time import sleep
import daemon
import logging
import socket
import ssl


flag = "PRCD"

subject = "OOPS: email without PGP sent :("

# where do i need to look for the certification authority lists? this is SO
# dependent
cacertList = "/etc/ssl/certs/ca-certificates.crt"

# this var, that I should properly have called "wait_seconds" is the frequency
#  of checking again the mail times after times
howMuchdoIsleep_5hourADay = 120

# where do i store the superfreaking important log of this megasoftware?
whereDoILog = "onlyPGP.log"

# thie is the body of the mail we send back
sendBackTXT = """
Good morning:
This is an automated message, therefore you must NOT answer.

If you are reading this message it's because you sent an unencrypted email to
me. Since this email is not encrypted,  I'm going NOT going to answer, and
IT IS NOT guaranteed that this email is gonna be read at all.
At least, not by me. :)  This recipient does not accept unencrypted
email anymore, and therefore you are encouraged to send only encrypted
messages with PGP.

It easy to set up a PGP client for your daily usage, and it will protect YOUR
PRIVACY.


-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1.4.14 (GNU/Linux)

mQENBFLXCecBCADMBFpbQtqFdHQ/4mUv2klyDFURpBqjOXxlIlNDgQB2D+SsCJYD
cxmalIl5jvUzlXBgwz+UtcziOieBhCbFyO4d2jyRHI5KIC7OMBY9Bbb95sDL20Q4
5vYZoOtJJU7QB7z2fceXcXXMu6hLMctsUi+vdyvlHQAz5hw8LhQFJ411DKa4SI/3
0KOHH4KXstU34rMHiMO6pa1UVd/2j9ARkFnvmCxjD8R/tNE946gGNREXkJF1DDhi
9qaowauC2HaEdOTeys21ORnyrxUOKqerar77ayTKwtDSR+1GGEFVnU/kRgFCEkS+
faslB/WwRLkrgsXeqpP5XRAVFrC1HyhVSUDnABEBAAG0J0FsZXNzYW5kcm8gKDE0
KSA8YWxlc3NhbmRyb0BsdW9uZ28ucHJvPokBPgQTAQIAKAUCUtcJ5wIbIwUJAeEz
gAYLCQgHAwIGFQgCCQoLBBYCAwECHgECF4AACgkQwoivufGXbMuaoggAv29GkAqw
J00cGBlWu4K22PCaJ6nqqztaq3QXqo7neI9Zmgp0IFuO6b7CJ6edZOyuzyol6mlB
8e3I3EbluI0GT9YXbmL1J/WxXGqmESrSBxrsujW3ZYwcmqN+3Yrcj43zf7Po986f
s/rY++/trwshHj97w0RYv9QeHSeq9atzVHRCiT9ZCgY6e3wMlwSjP6GhZ/pVJKiQ
zLfnXXyvj7xBvWQaXQL5DwFE2HVPMIHoDeRZi1sJDx2QGLnZYIVlVVsuN4G2gJ9X
YcRZbdSxdkk2uDU5OPffWY6y6xnc8iMMnP4WnfwjKKkD83ptEeLCKl4tMlltk/wZ
soXTWI3x3jaICLkBDQRS1wnnAQgA23SN5rGLIgEU7JWrbFl6M+5SOk6q+53hLT1Y
L4+72qqakToyF92Mg/luFz9W4ZkVvBIEJn6A9u0XdUNMrRgJNVHbXXudHS3rKtuR
KhR4yZeJ8kJm0b2lf1Xm9JxUH6J0tJos/48cuNVVpaUMI0rfNC4+OrYsBT66KeiW
AxtjXRrFV+j+jzp35CiytUX6iBr4w1zEZKxMxdLaYlRYzVGBAdAK8T0iJOgAp0/X
qKSPKb5LUvu0V1FMTHuPzadVKLBOtwGt0NxXrbgRJxZ/RMfSybEamYpRcxfIVE30
zwKnHQjVsOvfIC3wXCBjS/ImHeAUlEI7uGWoWvtksfnQu3LWEQARAQABiQElBBgB
AgAPBQJS1wnnAhsMBQkB4TOAAAoJEMKIr7nxl2zLG3QH/RIALvUSo84Kk11+94J/
MrHU0Q1IfRUQecxDmaH5wkYOzpld0bAbzeYA+V9uSHvV1u4id6gvS1htKIlOdRLo
mqrfJxfQ30JwLNcJjRTGg/xQTp4ny8bnXfxjYVSPiArlWcA9kdu2ZbLnhMUt/diL
9a+Kea2gRXUrYQoi9BKzmYdsc2rwlBMW5ZIx1bQrUNOBzfky2bIP+BOjYy4F/eml
YUjaaKXu9LPDUPKwmmejQrRQ9BE/amzojdy1tOX7a3JwzPupu2kzfYs96DQf+iDu
G/2mWkZr3/G/wKyyUbPs7iBdd1i3JY2l1rX0DJPDcHLeKuv++DqSWH2btgmdORxa
S3w=
=EdOF
-----END PGP PUBLIC KEY BLOCK-----


The universe believes in encryption ~ Assange.

Alessandro Luongo"""

logger = logging.getLogger()
# in normal operation mode, set this to INFO, or WHATEVER.
logger.setLevel(logging.INFO)
fh = logging.FileHandler(whereDoILog)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)


# stuff for preserving the logger handler instance when this sw becomes a demon
context = daemon.DaemonContext(
    files_preserve=[
        fh.stream,
    ],
)


# http://superuser.com/questions/97201/\
# how-to-save-a-remote-server-ssl-certificate-locally-as-a-file
# http://stackoverflow.com/questions/7885785/using-openssl-to-get-the\
# -certificate-from-a-server
# http://stackoverflow.com/questions/11884704/how-to-set-find-the-ca-certs\
# -argument-in-python-ssl-wrap-socket
# http://stackoverflow.com/questions/9713055/certificate-authority-for\
# -imaplib-and-poplib-python
# http://docs.python.org/2/library/ssl.html


class IMAP4_SSL_CA_CHECKER(imaplib.IMAP4_SSL):
    def open(self, host='imap.gmail.com', port=993,
             ca_certs='/etc/ssl/certs/ca-certificates.crt'):
        self.host = host
        self.port = port
        self.sock = socket.create_connection((host, port))
        self.sslobj = ssl.wrap_socket(self.sock, cert_reqs=ssl.CERT_REQUIRED,
                                      ca_certs=ca_certs)
        self.file = self.sslobj.makefile('rb')


def extract_body(payload):
    """
    http://unlogic.co.uk/posts/parsing-email-in-python.html
    """
    if isinstance(payload, str):
        return payload
    else:
        return '\n'.join([extract_body(part.get_payload())
                          for part in payload])


def sendBack(to, password):
    """
    Just send our default template+key+instruction
    """
    sender = Username
    receivers = [to]

    MESSAGE = """\From: %s\nTo: %s\nSubject: %s\n\n%s""" % (sender,
                                    ", ".join(receivers), subject, sendBackTXT)

    try:
        smtpObj = smtplib.SMTP(host='smtp.gmail.com', port=587)
        smtpObj.starttls()
        smtpObj.ehlo()
        smtpObj.login(Username, password)
        smtpObj.sendmail(Username, receivers, MESSAGE)
        smtpObj.quit()
        logger.info("Email sent")
    except Exception as e:
        logger.debug("Error: unable to send email -> %s" % e)
    return


def setFlagLastMail():
    """ Set the last received email with our flag """
    ids = data[0]  # data is a list.
    id_list = ids.split()  # ids is a space separated string
    latest_email_uid = id_list[-1]  # get the latest
    a, b = mail.uid('STORE', latest_email_uid, 'X-GM-LABELS', "%s" % flag)
    logger.info("Last email %s, has our flag %s" % (latest_email_uid, flag))
    # logger.debug( "".join([a,b]))
    return


def checkPGP(uidMail):
    """
    Check if an email has something inside with PGP (or signature)
    the input is a uid of your email
    """
    # store the flag of the email (seen vs unseen)

    results, data = mail.uid('fetch', uidMail, '(RFC822)')
    raw_email = data[0][1]
    emailOK = email.message_from_string(raw_email)

    # since for checking for trace of PGP we must download the email,
    # restore the previous state.
    # if stordFlag = unseen, then:
    mail.uid('STORE', uidMail, '-FLAGS', '(\Seen)')

    payloadString = ''
    # if( emailOK.is_multipart() == False ):
    #    #print "is_multipart is false: ", emailOK.is_multipart()
    #    payloadString=emailOK.get_payload()
    # if (emailOK.is_multipart() == True):
    #    #print "is_multipart is true: ", emailOK.is_multipart()
    #    print "Messeggio"
    #    print emailOK.get_payload()[1]
    #    payloadString=emailOK.get_payload()[1]
    #    print "----"

    payloadString = extract_body(emailOK.get_payload())

    match = re.search(r'BEGIN PGP(.*)END PGP', payloadString, re.M | re.DOTALL |
                        re.I)
    if (match):
        logger.info("Thank God, someone sent encrypted mail")
        return 0
    else:
        logger.debug("Nope. let's get mad with %s" % emailOK['From'])
        return emailOK['From']


############################################################
############################################################
############################################################
if __name__ == '__main__':
    Username = ''
    Password = ''
    try:
        Username = sys.argv[1]
        print "Prompt the password for you email: ",
        Password = getpass.getpass()
    except:
        print "Usage:  'python onlyPGPplz.py email@account.com'"

    context.open()
    logger.debug("Succesfull become a Deamon")

    logger.debug("Connecting to your email")
    try:
        mail = IMAP4_SSL_CA_CHECKER(host='imap.gmail.com', port="993")
    except Exception as e:
        logger.error("Could not log to imap because %s" % e)
        # sys.exit()

    mail.login(Username, Password)
    mail.list()
    mail.select("inbox")
    logger.debug("Connecting to inbox")
    results, data = mail.uid('search', None, "ALL")

    logger.info("Setting flag to last email - Start patroling")
    setFlagLastMail()

    while (True):
        nuove = []
        breakVar = 0
        logger.debug("----------------")
        results, data = mail.uid('search', None, "ALL")
        for x in reversed(data[0].split()):
            logger.debug("Checking email: %s" % x)
            t, d = mail.uid('FETCH', x, '(X-GM-LABELS)')
            for lab in d:
                match = re.search(r"%s" % flag, lab, re.M | re.I)
                if (match):
                    breakVar = 1
                    logger.debug("Found flagged email.")
                    # this email has our label, so it's the last one since
                    # we checked. all the email before this are already
                    # checked.
                else:
                    logger.debug("Found new mail since last time")
                    # this email has been received after our last check.
                    # it's new and therefore must be checked
                    nuove.append(x)
            if (breakVar == 1): break

        logger.debug("Checking for PGP signature in new email (%s): " %
                     len(nuove))
        for x in nuove:
            logger.debug("Checking signature in %s" % x)
            res = checkPGP(x)
            if (res != 0):
                sendBack(res, Password)

        setFlagLastMail()
        logger.debug("Sleeping...")
        sleep(howMuchdoIsleep_5hourADay)
