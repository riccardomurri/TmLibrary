from . import __version__
from .cli import Imextract


parser, subparsers = Imextract.get_parser_and_subparsers()

parser.description = '''
        Extract images from heterogeneous microscopic image file formats
        using the Bio-Formats library.
    '''
parser.version = __version__

init_parser = subparsers.choices['init']
init_parser.add_argument(
    '-b', '--batch_size', type=int, default=10,
    help='number of image files that should be processed per job'
         '(default: 10)')
init_parser.add_argument(
    '-p', '--projection', action='store_true',
    help='when maximum intensity project should be performed')

for name in subparsers.choices:
    subparsers.choices[name].set_defaults(handler=Imextract.call)
