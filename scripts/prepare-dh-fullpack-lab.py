"""Prepare only; never starts a runtime or downloads dependencies."""
import argparse
import json
from pathlib import Path
from dh_fullpack_lab import policy
from dh_fullpack_lab.prepare import prepare

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server-source', default='D:/proyectos/mc-server')
    parser.add_argument('--client-source', default='C:/Users/zulia/AppData/Local/Virgos-MC/juego')
    parser.add_argument('--pack-source', required=True, help='Authorized source snapshot with pack overrides')
    parser.add_argument('--artifacts', required=True, help='Verified compat-manifest.json directory, including observer QA jar if needed')
    parser.add_argument('--lab', required=True, help='New external directory; must not exist or overlap any input')
    parser.add_argument('--java-server', required=True)
    parser.add_argument('--java-client', required=True)
    parser.add_argument('--skin-fixture', action='store_true',
                        help='Use the public Notch nickname for client2 only in the pinned isolated skins lab')
    args = parser.parse_args()
    try:
        if not policy.authorized_lab(args.lab):
            raise ValueError('Only the explicitly authorized full-pack destination is permitted')
        result = prepare(args.server_source, args.client_source, args.pack_source, args.artifacts,
                         args.lab, args.java_server, args.java_client, skin_fixture=args.skin_fixture)
        print(json.dumps({'phase': 'prepared', 'lab': result['lab'], 'copiedBytes': result['copiedBytes'],
                          'omitted': result['omitted']}))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, 'Preparation refused: ' + str(error) + '\n')
