from supabase_auth import SyncSupportedStorage

class MyAwesomeStorage(SyncSupportedStorage):
    def __init__(self) -> None:
        print("Initializing a new storage")
        self.data = {}

    def get_item(self, key: str):
        print("GetItemStorageSize: ", len(self.data))
        if key in self.data:
            return self.data[key]
        return None

    def set_item(self, key: str, value: str) -> None:
        self.data[key] = value
        print("AfterAdding: Storage size: ", len(self.data))

    def remove_item(self, key: str) -> None:
        if key in self.data:
            self.data.pop(key)
        print("Afterdeleteing: storage size ", len(self.data))