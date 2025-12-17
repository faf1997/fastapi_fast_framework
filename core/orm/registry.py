class Registry:
    _instance = None
    _models = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Registry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def add(cls, name, model_class):
        cls._models[name] = model_class

    @classmethod
    def get(cls, name):
        return cls._models.get(name)

    @classmethod
    def models(cls):
        return cls._models
