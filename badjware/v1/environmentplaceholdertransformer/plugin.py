import os
import sys
import yaml
import re

from types import SimpleNamespace
from base64 import b64encode, b64decode

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import common as c

PLACEHOLDER_PROG = re.compile(r'\$\{\s*env:([a-zA-Z0-9_]+)\s*\}')

def load_config():
    """
    Load plugin configurations.
    :return: a namespace containing the configurations
    :rtype: SimpleNamespace
    """
    # load
    with open(sys.argv[1], 'r') as f:
        plugin_config = yaml.safe_load(f)
        resource_selectors = plugin_config.get('resourceSelectors', [])

    return SimpleNamespace(
        resource_selectors=resource_selectors
    )

def run_plugin():
    """
    Perform arbitrary key/value replacements in kubernetes resources.
    """
    # load config
    config = load_config()
    all_resources = []

    for resource in yaml.safe_load_all(sys.stdin.read()):
        is_resource_match, resource_metadata = c.resource_match_selectors(resource, config.resource_selectors)
        if is_resource_match:
            for key, value in resource.items():
                # secret is a special case
                if(resource_metadata['kind'] == 'Secret'):
                    if 'data' in resource:
                        resource['data'] = c.perform_placeholder_replacements(resource['data'], PLACEHOLDER_PROG, c.get_default_replacement_func(os.environ), True)
                    if 'tls' in resource:
                        resource['tls'] = c.perform_placeholder_replacements(resource['tls'], PLACEHOLDER_PROG, c.get_default_replacement_func(os.environ), True)
                # exclude these top-level fields from placeholder replacement
                elif key not in ('apiVersion', 'kind', 'metadata'):
                    resource[key] = c.perform_placeholder_replacements(value, PLACEHOLDER_PROG, c.get_default_replacement_func(os.environ), False)

        all_resources.append(resource)
    yaml.dump_all(all_resources, sys.stdout, default_flow_style=False)
