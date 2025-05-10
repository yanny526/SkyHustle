# googleapiclient/discovery.py

def build(*args, **kwargs):
    """
    Stub for googleapiclient.discovery.build
    Returns a minimal service object with spreadsheets().values().get/append/update stub methods.
    """
    class DummyService:
        def spreadsheets(self):
            return self

        def values(self):
            return self

        def get(self, *args, **kwargs):
            class Exec:
                def execute(self):
                    return {"values": []}
            return Exec()

        def append(self, *args, **kwargs):
            class Exec:
                def execute(self):
                    return {}
            return Exec()

        def update(self, *args, **kwargs):
            class Exec:
                def execute(self):
                    return {}
            return Exec()

    return DummyService()
