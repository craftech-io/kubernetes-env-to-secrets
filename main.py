import argparse
import sys
import base64
import json
from string import Template

parser = argparse.ArgumentParser(description='Convert environment files to kubernetes secrets')
parser.add_argument('--name', metavar='name', nargs='?', type=str, default='my-secrets', help='Name of the secret store')
parser.add_argument('--env', metavar='.env', nargs='?', type=argparse.FileType('r'), default=sys.stdin, help='Environment input file, stdin by default')
parser.add_argument('--secrets', metavar='.yaml', nargs='?', type=argparse.FileType('w'), default=sys.stdout, help='Secrets output file, stdout by default')


def loadFiles(secret):
    if (secret[1].startswith('filecontent=')):
        with open(secret[1][12:], 'r') as secretfile:
            data = secretfile.read()
        return [secret[0], data]
    return secret

def yaml_ouput(encodedSecrets):
    '''secrets its a tuple with key, value format'''

    yamlTemplate = Template("""
apiVersion: v1
kind: Secret
metadata:
  name: $name
type: Opaque
data:
$encodedSecrets""")
    yamlOutput = yamlTemplate.substitute(name=args.name, encodedSecrets='\n'.join(encodedSecrets))

    args.secrets.write(yamlOutput)
    args.secrets.close()

def process_plainfile(args):
    config_lines = args.env.readlines()
    args.env.close()
    secrets = [line.split('=', 1) for line in config_lines]
    secrets = map(loadFiles, secrets)

    encodedSecrets = ['  {0}: {1}'.format(
        secret[0],
        base64.b64encode(secret[1].replace('\n', '').encode('utf-8')).decode('utf-8')
    ) for secret in secrets]

    yaml_ouput(encodedSecrets)

def process_json(args):
    json_dict = json.loads(args.env.read())
    args.env.close()
    secrets = list(json_dict.items())
    encodedSecrets = [
        '  {0}: {1}'.format(
                secret[0],
                base64.b64encode(str(secret[1]).encode('utf-8')).decode('utf-8')
        )
    for secret in secrets]
    yaml_ouput(encodedSecrets)

if __name__ == '__main__':
    args = parser.parse_args()
    if args.env.name.endswith('.json'):
        process_json(args)
    else:
        process_plainfile(args)