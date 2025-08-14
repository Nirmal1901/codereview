
class Car():
    def __init__(self, brand=None, model=None):
        self.brand = brand if brand else "Unknown"
        self.model = model if model else "Unknown"

    def set_brand(self, brand):
        self.brand = brand

    def get_brand(self):
        return self.brand

    def set_model(self, model):
        
        self.model = model

    def get_model(self):
        return self.model
