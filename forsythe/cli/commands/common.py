import os


class Command(object):

    @classmethod
    def init_parser(cls, parser):
        pass

    @classmethod
    def run(cls, args):
        raise NotImplementedError
