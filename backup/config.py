class Config:
    config = None

    @classmethod
    def get(cls, name):
        if cls.config is None:
            cls.load()

        return cls.config[name]

    @classmethod
    def load(cls):
        """ Loads or reloads configuration from environment variables
        """
        cls.config = {}
