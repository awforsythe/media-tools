import os
import lxml.etree as etree


def get_eos_config_path():
    canon_appdata = os.path.expandvars('%LOCALAPPDATA%\\Canon_INC')
    if not os.path.isdir(canon_appdata):
        raise RuntimeError("Canon settings directory not found: %s" % canon_appdata)

    dirnames = [f for f in os.listdir(canon_appdata) if f.startswith('EOS_Utility_3.exe') and os.path.isdir(os.path.join(canon_appdata, f))]
    if not dirnames:
        raise RuntimeError("Could not find EOS_Utility_3.exe config dir within %s" % canon_appdata)
    if len(dirnames) > 1:
        raise RuntimeError("Multiple EOS_Utility_3.exe config dirs found within %s" % canon_appdata)

    eos_dirpath = os.path.join(canon_appdata, dirnames[0])
    dirnames = [f for f in os.listdir(eos_dirpath) if os.path.isdir(os.path.join(eos_dirpath, f))]
    if not dirnames:
        raise RuntimeError("Could not find version config dir within %s" % eos_dirpath)
    if len(dirnames) > 1:
        raise RuntimeError("Multiple version config dirs found within %s" % eos_dirpath)

    config_filepath = os.path.join(eos_dirpath, dirnames[0], 'user.config')
    if not os.path.isfile(config_filepath):
        raise RuntimeError("Could not find user.config file for EOS Utility 3: %s" % config_filepath)

    return config_filepath


def update_eos_config(output_dirpath, prefix, start_number):
    filepath = get_eos_config_path()
    tree = etree.parse(filepath)
    root = tree.getroot()

    app_settings = root.xpath('userSettings/EOSUtility.AppSettings')[0]
    for setting in app_settings.getchildren():
        name = setting.get('name')
        if name == 'SaveFolder':
            setting.xpath('value')[0].text = output_dirpath
        elif name == 'FileNamePrefix':
            setting.xpath('value')[0].text = prefix
        elif name == 'FileNameNumber':
            setting.xpath('value')[0].text = str(start_number)
        elif name == 'FileNameFigure':
            setting.xpath('value')[0].text = '4'
        elif name == 'FolderNameSeparator':
            setting.xpath('value')[0].text = '1'
        elif name == 'FileNameSeparator':
            setting.xpath('value')[0].text = '2'
        elif name == 'FileCustomizeIndex':
            setting.xpath('value')[0].text = '1'

    with open(filepath, 'w') as fp:
        fp.write(str(etree.tostring(tree, pretty_print=True), 'utf-8'))


def get_image_filepath(image_num):
    filepath = get_eos_config_path()
    tree = etree.parse(filepath)
    root = tree.getroot()

    output_dirpath = None
    prefix = None
    figure = None

    app_settings = root.xpath('userSettings/EOSUtility.AppSettings')[0]
    for setting in app_settings.getchildren():
        name = setting.get('name')
        if name == 'SaveFolder':
            output_dirpath = setting.xpath('value')[0].text
        elif name == 'FileNamePrefix':
            prefix = setting.xpath('value')[0].text
        elif name == 'FileNameFigure':
            figure = int(setting.xpath('value')[0].text)

    assert all(x is not None for x in (output_dirpath, prefix, figure))
    filename_pattern = prefix + '%0' + str(figure) + 'd.CR2'
    return os.path.join(output_dirpath, filename_pattern % image_num)
