# Suppress warnings
import warnings
warnings.filterwarnings(
    'ignore',
    message='^`NoneType` object ',
    module='^dataclasses_json\.',
    category=RuntimeWarning)

import sys

from . import arguments
from . import config


def main():
    result = arguments.parse(sys.argv[0], sys.argv[1:])
    if not result.success:
        # Arguments is not valid.
        # Show error messages and exit.
        sys.stderr.write(result.output)
        return arguments.ExitInvalidArgs

    conf_file, conf = config.load_or_default()
    ca = arguments.CommandArgs(
        args=sys.argv,
        ns=result.ns,
        conf=conf,
        conf_file=conf_file,
    )
    return result.ns.fn(ca)
