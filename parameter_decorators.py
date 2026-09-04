# Stub for parameter_decorators
import functools

def parameter_decorator(*args, **kwargs):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*a, **kw):
            return func(*a, **kw)
        return wrapper
    return decorator
