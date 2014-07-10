__author__ = 'julz'
from collections import OrderedDict
def get_data_order(dataformatdef):
    """
    >>> get_data_order([{'name': 'V&A', 'user': 'vamuseum', 'id': '390861362'}])
    ['vamuseum']
    >>> get_data_order([{'name': 'V&A', 'user': 'vamuseum', 'id': '390861362'},{'name': 'V&A', 'user': 'vashop', 'id': '390861362'}])
    ['vamuseum', 'vashop']
    """
    try:
        return [i['user'] for i in dataformatdef]
    except TypeError:
        return []

def convert_date_indexed_dict_to_list(date_dict):
    """
    >>> convert_date_indexed_dict_to_list({'1234':[11,22,33]})
    [['1234', 11, 22, 33]]
    >>> convert_date_indexed_dict_to_list({1234:[11,22,33],1235:[111,222,333]})
    [[1234, 11, 22, 33], [1235, 111, 222, 333]]
    """
    r = [[datum] + date_dict[datum] for datum in date_dict]
    return r


def map_elements_for_chart(instagram_users=None, data=None):
    """
    >>> map_elements_for_chart([{'name': 'V&A', 'user': 'vamuseum', 'id': '390861362'}],[{u'_id': '53be9c603090781ac49d95b8', u'followers': 17550, u'user_account': u'vamuseum', u'service': u'instagram', u'datetime': 1405000800}])
    [[1405000800, 17550]]
    >>> map_elements_for_chart([{'name': 'V&A', 'user': 'vamuseum', 'id': '390861362'}, {'name': 'V&A Shop', 'user': 'v_and_a_shop', 'id': '390861456'}],[{u'_id': '53be9c603090781ac49d95b8', u'followers': 17550, u'user_account': u'vamuseum', u'service': u'instagram', u'datetime': 1405000800}])
    [[1405000800, 17550, None]]
    >>> map_elements_for_chart([{'name': 'V&A', 'user': 'vamuseum', 'id': '390861362'}, {'name': 'V&A Shop', 'user': 'v_and_a_shop', 'id': '390861456'}],[{u'_id': '53be9c603090781ac49d95b8', u'followers': 17550, u'user_account': u'vamuseum', u'service': u'instagram', u'datetime': 1405000800},{u'_id': '53bea23c3090781b672f229f', u'followers': 486, u'user_account': u'v_and_a_shop', u'service': u'instagram', u'datetime': 1405000800}])
    [[1405000800, 17550, 486]]
    >>> map_elements_for_chart([{'name': 'V&A', 'user': 'vamuseum', 'id': '390861362'}, {'name': 'V&A Shop', 'user': 'v_and_a_shop', 'id': '390861456'}],[{u'_id': '53be9c603090781ac49d95b8', u'followers': 17550, u'user_account': u'vamuseum', u'service': u'instagram', u'datetime': 1405000800},{u'_id': '53bea23c3090781b672f229f', u'followers': 486, u'user_account': u'v_and_a_shop', u'service': u'instagram', u'datetime': 1405000800},{u'_id': '53bea4943090781b672f22a4', u'followers': 17552, u'user_account': u'vamuseum', u'service': u'instagram', u'datetime': 1405002900},{u'_id': '53bea4943090781b672f22a5', u'followers': 486, u'user_account': u'v_and_a_shop', u'service': u'instagram', u'datetime': 1405002900}])
    [[1405000800, 17550, 486], [1405002900, 17552, 486]]
    >>> map_elements_for_chart([{'name': 'V&A', 'user': 'vamuseum', 'id': '390861362'}, {'name': 'V&A Shop', 'user': 'v_and_a_shop', 'id': '390861456'}],[{u'_id': '53be9c603090781ac49d95b8', u'followers': 17550, u'user_account': u'vamuseum', u'service': u'instagram', u'datetime': 1405000800},{u'_id': '53bea23c3090781b672f229f', u'followers': 486, u'user_account': u'v_and_a_shop', u'service': u'instagram', u'datetime': 1405000800},{u'_id': '53bea4943090781b672f22a4', u'followers': 17552, u'user_account': u'vamuseum', u'service': u'instagram', u'datetime': 1405002900},{u'_id': '53bea4943090781b672f22a5', u'followers': 486, u'user_account': u'v_and_a_shop', u'service': u'instagram', u'datetime': 1405002910}])
    [[1405000800, 17550, 486], [1405002900, 17552, None], [1405002910, None, 486]]
    """
    datacolumns = get_data_order(instagram_users)
    nocolumns = len(datacolumns)
    r = {}
    for datum in data:
        mycol = datacolumns.index(datum['user_account'])
        try:
            r[datum['datetime']][mycol] = datum['followers']
        except KeyError:
            r[datum['datetime']] = [None] * nocolumns
            r[datum['datetime']][mycol] = datum['followers']
    return convert_date_indexed_dict_to_list(r)
