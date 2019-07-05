import os

from forsythe.collections import load_collection, load_default_collection


class Command(object):

    @classmethod
    def init_parser(cls, parser):
        pass

    @classmethod
    def run(cls, args):
        raise NotImplementedError


class CollectionCommand(Command):

    @classmethod
    def init_parser(cls, parser):
        arg = lambda x: load_collection(os.path.abspath(x)) if x else load_default_collection()
        parser.add_argument('--collection', '-c', type=arg, default='')
