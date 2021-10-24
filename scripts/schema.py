import tempfile
import sys
import subprocess

from server.graphql.schema import schema


def main():
    if len(sys.argv) != 2:
        print()
        print('    Usage:')
        print('        schema --diff')
        print('        schema --write')
        print()
        sys.exit(-1)

    action = sys.argv[1]

    if action == '--diff':
        temp = tempfile.NamedTemporaryFile()
        with open(temp.name, 'w') as outfile:
            print(schema.as_str(), file=outfile)
            outfile.flush()

            proc = subprocess.Popen(['diff', '-u', 'schema.graphql', str(temp.name)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.wait()
            if proc.returncode != 0:
                print(proc.stdout.read().decode())
                print("Fix this with:")
                print()
                print("    $ schema --write")
                print()

    elif action == '--write':
        with open('schema.graphql', 'w') as outfile:
            print(schema.as_str(), file=outfile)

    else:
        print('Unknown flag:', action)
        print()
        print('    Usage:')
        print('        schema --diff')
        print('        schema --write')
        print()
        sys.exit(-1)
