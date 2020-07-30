import os
import sys
import hashlib
import yaml

from types import SimpleNamespace
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import common as c

def load_config():
    """
    Load plugin configurations.
    :return: a namespace containing the configurations
    :rtype: SimpleNamespace
    """
    # load
    with open(sys.argv[1], 'r') as f:
        plugin_config = yaml.safe_load(f)
        resources = plugin_config.get('resources', [])

    # validation
    validation_fail = False
    if not resources:
        c.eprint('resources is required')
        validation_fail = True
    for resource in resources:
        if 'url' not in resource:
            c.eprint('resources.url is required')
            validation_fail = True
            break
    if validation_fail:
        raise Exception()

    return SimpleNamespace(
        resources=resources
    )

def validate_sha256(source, data, expected):
    """
    Validate the sha256 checksum of some data. Exit validation failure.
    :param str source: the source of the data, appear in an error message on validation failure
    :param bytes data: the data to validate
    :param str expected: expected sha256 digest
    """
    sha256 = hashlib.sha256()
    sha256.update(data)
    actual = sha256.hexdigest()
    if expected != actual:
        c.eprint("sha256 checksum validation failed for", source)
        c.eprint("expected:", expected)
        c.eprint("actual:  ", actual)
        raise Exception()

def run_plugin():
    """
    Download kubernetes resources from a remote location
    """
    config = load_config()
    all_resources = []

    try:
        for resource in config.resources:
            url = resource['url']
            with urlopen(url) as f:
                data = f.read()
            if 'sha256' in resource:
                validate_sha256(url, data, resource['sha256'])
            all_resources = all_resources + list(yaml.safe_load_all(data))
    except yaml.YAMLError as e:
        c.eprint("%s: invalid yaml" % url)
        if hasattr(e, 'problem_mark'):
            c.eprint(e.problem_mark)
            c.eprint(e.problem)
            if e.context is not None:
                c.eprint(e.context)
        raise e
    except HTTPError as e:
        c.eprint("%s: %s %s" % (url, e.code, e.reason))
        raise e
    except URLError as e:
        c.eprint("%s: %s" % (url, e.reason))
        raise e
    yaml.dump_all(all_resources, sys.stdout, default_flow_style=False)