import lxml.etree as etree

__rdf__ = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}'
__dt__ = '{http://darktable.sf.net/}'


def increment_history_end(desc, delta):
    value = int(desc.get(__dt__ + 'history_end'))
    new_value = value + delta
    desc.set(__dt__ + 'history_end', str(new_value))



def configure_iop_li(li, iop):
    li.set(__dt__ + 'operation', iop.operation)
    li.set(__dt__ + 'enabled', '1')
    for attr in ('modversion', 'params', 'multi_name', 'multi_priority', 'blendop_version', 'blendop_params'):
        li.set(__dt__ + attr, str(getattr(iop, attr)))


def edit_xmp(xmp_filepath, iops):
    if not iops:
        return

    tree = etree.parse(xmp_filepath)
    root = tree.getroot()
    desc = root.getchildren()[0].getchildren()[0]

    increment_history_end(desc, len(iops))

    history = desc.find(__dt__ + 'history')
    seq = history.find(__rdf__ + 'Seq')

    for iop in iops:
        li = etree.SubElement(seq, __rdf__ + 'li')
        configure_iop_li(li, iop)

    with open(xmp_filepath, 'w') as fp:
        fp.write(str(etree.tostring(tree, pretty_print=True), 'utf-8'))
