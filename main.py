import argparse
import sys
import base64
import json
from string import Template
import re

parser = argparse.ArgumentParser(description='Convert environment files to kubernetes secrets')
parser.add_argument('--name', metavar='name', nargs='?', type=str, default='my-secrets',
                    help='Name of the secret store')
parser.add_argument('--env', metavar='.env', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
                    help='Environment input file, stdin by default')
parser.add_argument('--secrets', metavar='.yaml', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                    help='Secrets output file, stdout by default')

env_regex = re.compile(r'^(?P<variable>[a-zA-Z]\w*)\s*=\s*(?P<value>.*?)\s*?(?P<comment>#.*?)?$')


def load_files(secret):
    if secret[1].startswith('filecontent='):
        with open(secret[1][12:], 'r') as secretfile:
            data = secretfile.read()
        return [secret[0], data]
    return secret


def yaml_ouput(encoded_secrets):
    """secrets its a tuple with key, value format"""

    yaml_template = Template("""
apiVersion: v1
kind: Secret
metadata:
  name: $name
type: Opaque
data:
$encodedSecrets""")
    yaml_output = yaml_template.substitute(name=args.name, encodedSecrets='\n'.join(encoded_secrets))

    args.secrets.write(yaml_output)
    args.secrets.close()


def process_plainfile(_args):
    config_lines = _args.env.read().splitlines()
    _args.env.close()
    secrets = []
    for line in config_lines:
        m = env_regex.match(line)
        if m:
            secrets.append((m.group('variable'), m.group('value')))
    secrets = map(load_files, secrets)
    encoded_secrets = ['  {0}: {1}'.format(
        secret[0],
        base64.b64encode(secret[1].replace('\n', '').encode('utf-8')).decode('utf-8')
    ) for secret in secrets]

    yaml_ouput(encoded_secrets)


def process_json(_args):
    json_dict = json.loads(_args.env.read())
    _args.env.close()
    secrets = list(json_dict.items())
    encoded_secrets = [
        '  {0}: {1}'.format(
            secret[0],
            base64.b64encode(str(secret[1]).encode('utf-8')).decode('utf-8')
        )
        for secret in secrets]
    yaml_ouput(encoded_secrets)


if __name__ == '__main__':
    args = parser.parse_args()
    if args.env.name.endswith('.json'):
        process_json(args)
    else:
        process_plainfile(args)
