import re

from forsythe.darktable.data import Struct


class dt_iop(Struct):

    modversion = 5
    multi_name = ''
    multi_priority = 0
    blendop_version = 8
    blendop_params = 'gz11eJxjYGBgkGAAgRNODGiAEV0AJ2iwh+CRxQcA5qIZBA=='

    __operation_regex__ = re.compile(r'dt_iop_(.*)_params_t')

    @property
    def operation(self):
        if hasattr(self, '__operation__'):
            return self.__operation__
        match = self.__operation_regex__.match(self.__class__.__name__)
        if not match:
            raise ValueError('%s has no __operation__ name override and is not named dt_iop_<operation>_params_t' % self.__class__.__name__)
        return match.group(1)

    @property
    def params(self):
        return self.encode()


class dt_iop_clipping_params_t(dt_iop):
    __attrs__ = '''
        float angle, cx, cy, cw, ch, k_h, k_v;
        float kxa, kya, kxb, kyb, kxc, kyc, kxd, kyd;
        int k_type, k_sym;
        int k_apply, crop_auto;
        int ratio_n, ratio_d;
    '''

    def __init__(self):
        super().__init__()
        self.cw = 1.0
        self.ch = 1.0
        self.kxa = 0.2
        self.kya = 0.2
        self.kxb = 0.8
        self.kyb = 0.2
        self.kxc = 0.8
        self.kyc = 0.8
        self.kxd = 0.2
        self.kyd = 0.8
        self.crop_auto = 1


class dt_iop_exposure_params_t(dt_iop):
    __attrs__ = '''
        int mode;
        float black;
        float exposure;
        float deflicker_percentile, deflicker_target_level;
    '''

    def __init__(self):
        super().__init__()
        self.mode = 0
        self.black = 0.0
        self.exposure = 0.0
        self.deflicker_percentile = 50.0
        self.deflicker_target_level = -4.0
