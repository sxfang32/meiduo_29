def get_breadcrumb(cat3):
    """包装指定类别的面包屑"""
    cat1 = cat3.parent.parent
    # 给一级类别定义URL属性
    cat1.url = cat1.goodschannel_set.all()[0].url

    # 包装面包屑导航数据
    breadcrumb = {
        'cat1': cat3.parent.parent,
        'cat2': cat3.parent,
        'cat3': cat3
    }
    return breadcrumb
