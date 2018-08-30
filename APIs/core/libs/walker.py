#!/usr/bin/env python

import hashlib
import os
import sys

import magic

import yara


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def walk(rootdir, rules, extensions=('.aspx', '.cs')):
    r = {}
    if type(extensions) != tuple:
        extensions = tuple(map(str.strip, extensions.split(',')))
    for subdir, dirs, files in os.walk(rootdir):
        for file in files:
            if file.endswith(extensions):
                with open(os.path.join(subdir, file), 'rb') as f:
                    f = f.read()

                matches = rules.match(data=f)
                if matches:
                    tags = ", ".join(i.rule for i in matches)
                    yara_patterns = "\n\n".join(
                        map(lambda x: "\n".join(
                            map(str, x.strings)), matches))

                    filesize = sizeof_fmt(
                        os.path.getsize(os.path.join(subdir, file)))
                    fileExtension = os.path.join(
                        subdir, file).split('.')[-1]
                    fileType = magic.from_file(os.path.join(subdir, file))
                    md5sum = hashlib.md5(f).hexdigest()
                    sha256sum = hashlib.sha256(f).hexdigest()

                    r[os.path.join(subdir, file)] = {
                        'filesize': filesize,
                        'fileExtension': fileExtension,
                        'fileType': fileType,
                        'md5sum': md5sum,
                        'sha256sum': sha256sum,
                        'yara_tags': tags,
                        'yara_patterns': yara_patterns,
                        'fileContent': f,
                    }
    return r


def main():
    if len(sys.argv) != 3:
        exit('[!] {} <directory> <yara_rule>'.format(sys.argv[0]))

    yara_rules = yara.compile(sys.argv[2])
    r = walk(rootdir=sys.argv[1], rules=yara_rules)
    for k, v in r.items():
        print k,  ", ".join(v['yara_patterns'].split())


if __name__ == '__main__':
    main()
