
class Stream(object):
    """A livestream object."""
    def __init__(self, **kwargs):
        self.url = kwargs.get('url')
        self.viewers = kwargs.get('viewers')
        self.display_name = kwargs.get('display_name')
        self.game = kwargs.get('game')
        self.status = kwargs.get('status').encode('utf-8').strip()
