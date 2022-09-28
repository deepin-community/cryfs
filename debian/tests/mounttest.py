#!/usr/bin/python3

import shutil
import subprocess
import time
from pathlib import Path

import pexpect

# Set up the environment
mntpath = Path("/tmp/mnt")
basepath = Path("/tmp/base")
testfilepath = mntpath / "foo"
testtext = "bar"
password="password"


def umount(path):
    try:
        subprocess.run(
            "fusermount -u {}".format(str(path)).split(),
            capture_output=True,
        )
        time.sleep(1)
    except FileNotFoundError:
        pass


def cleanup():
    umount(mntpath)

    for path in [mntpath, basepath]:
        if path.exists():
            shutil.rmtree(str(path))

        path.mkdir()


print("Initial cleanup")
cleanup()

print("Create an encrypted volume")
session = pexpect.spawn(
    "cryfs --allow-replaced-filesystem {0} {1}".format(
        str(basepath), str(mntpath)
    )
)

session.expect("Your choice")
session.sendline("y")
session.expect("Password:", timeout=600)
session.sendline(password)
session.expect("Confirm Password:", timeout=600)
session.sendline(password)
session.expect(pexpect.EOF, timeout=600)

print("Test the volume")
assert not testfilepath.exists()
testfilepath.write_text(testtext)
assert testfilepath.exists()
assert testfilepath.read_text() == testtext

print("Unmount and test")
umount(mntpath)
time.sleep(1)
assert not testfilepath.exists()

print("Remount and test")
session = pexpect.spawn("cryfs {0} {1}".format(str(basepath), str(mntpath)))
session.expect("Password:")
session.sendline(password)
session.expect(pexpect.EOF)

assert testfilepath.exists()
assert testfilepath.read_text() == testtext

print("Final cleanup")
cleanup()
mntpath.rmdir()
basepath.rmdir()
