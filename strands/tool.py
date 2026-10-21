def tool(func):
    """
    Custom decorator for defining agent tools.
    """
    func.is_tool = True
    return func