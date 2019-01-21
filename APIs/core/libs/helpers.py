import subprocess


def is_valid_mountpoint(share_path):
    try:
        c = subprocess.check_call(
            ["timeout", "5", "mountpoint", "-q", share_path.rstrip('/')])
    except subprocess.CalledProcessError:
        c = 1
    if c == 0:
        return True
    return False
