import yaml
import json
from os.path import join as pjoin
import bitmath
from pandas import NaT


def get_specs(f_yaml):
    """
    Parse specs from yaml file name to dict
    """
    with open(f_yaml, 'r') as f:
        specs = yaml.safe_load(f)
    return specs


def store_var(name, value, parent='artifacts'):
    with open(pjoin(parent, name), 'w') as f:
        if isinstance(value, str):
            f.write(value)
        elif isinstance(value, list):
            for v in value:
                assert isinstance(v, str)
                f.write(v.strip() + '\n')
        else:
            raise NotImplementedError


def read_var(name, parent='artifacts'):
    with open(pjoin(parent, name), 'r') as f:
        content = f.read()

    if '\n' not in content:
        return content
    else:
        return content.split('\n')[:-1]


def store_dict(name, value, parent='artifacts'):
    with open(pjoin(parent, name), 'w') as f:
        json.dump(value, f, indent=2)


def bytes_to_hstring(n_bytes):
    return (
        bitmath.Byte(int(n_bytes))
        .best_prefix(bitmath.SI)
        .format("{value:.1f} {unit}")
    )


def strfdelta(tdelta):
    s = ""
    if tdelta is NaT:
        return s

    days = tdelta.days
    hours, rem = divmod(tdelta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)

    if days:
        s = f"{days}d"
    if hours:
        s += f"{hours}h"
    if minutes:
        s += f"{minutes}m"

    return s + f"{seconds}s"
