import typing

def is_optional(annotation):
    try:
        origin = annotation.__origin__
    except AttributeError:
        return False

    if origin is not typing.Union:
        return False

    return annotation.__args__[-1] is type(None)

def _cast(key, value, cls):
    try:
        # Check if it's typing.List
        if cls.__origin__ is list:
            if not isinstance(value, list):
                raise TypeError(f'Expected list for {key!r} but got {value.__class__!r} instead')

            typed = cls.__args__[0]
            return [_cast(key, v, typed) for v in value]
        elif cls.__origin__ is typing.Union and cls.__args__[-1] is type(None):
            # typing.Optional[X]
            typed = cls.__args__[0]
            if isinstance(value, type(None)):
                return value
            return _cast(key, value, typed)
    except AttributeError:
        pass

    if isinstance(value, cls):
        return value
    else:
        try:
            return cls(value)
        except Exception as e:
            raise TypeError(f'Failed to convert {key!r} to {cls!r}.') from e

def _verify_at_init(self, data):
    annotations = type(self).__annotations__
    for key, typed in annotations.items():
        try:
            value = data[key]
        except KeyError:
            if not is_optional(typed):
                raise TypeError(f'Required key {key!r} of type {typed!r} not found.') from None
            else:
                setattr(self, key, None)
        else:
            attempt = _cast(key, value, typed)
            setattr(self, key, attempt)

def convert(value):
    try:
        f = value.to_dict
    except AttributeError:
        return value
    else:
        return f()

def to_dict(self):
    ret = {}
    for key in self.__slots__:
        value = getattr(self, key)
        if isinstance(value, list):
            ret[key] = [convert(v) for v in value]
        else:
            ret[key] = convert(value)
    return ret

class ConfigMeta(type):
    def __new__(metacls, name, base, attrs):
        try:
            keys = set(attrs['__annotations__'])
        except KeyError:
            raise TypeError('Must have annotations at the top level.') from None

        if not keys.isdisjoint(attrs):
            raise TypeError('Potential shadowing going on.')

        attrs['__slots__'] = keys
        attrs['__init__'] = _verify_at_init
        attrs['to_dict'] = to_dict
        return super().__new__(metacls, name, base, attrs)

class SubredditWidgetConfig(metaclass=ConfigMeta):
    name: str
    table: bool

class SubredditConfig(metaclass=ConfigMeta):
    format: dict
    top_cut: int
    wiki: str
    name: str
    widget: typing.Optional[SubredditWidgetConfig]
    maximum: typing.Optional[int]
    minimum: typing.Optional[int]
    minimum_record: typing.Optional[str]
    maximum_record: typing.Optional[str]
    game_ids: typing.Optional[dict]

class Config(metaclass=ConfigMeta):
    client: str
    user_agent: str
    username: str
    password: str
    twitch_client_id: str
    twitch_client_secret: str
    secret: str
    delay: int
    subreddits: typing.List[SubredditConfig]
