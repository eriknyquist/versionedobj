from versionedconfig import VersionedConfig, CustomValue

class TestValue(CustomValue):
    def __init__(self):
        self.a = 1
        self.b = 2
        self.c = 3

    def to_dict(self):
        return f"{self.a}:{self.b}:{self.c}"

    def from_dict(self, value):
        self.a, self.b, self.c =  [int(x) for x in value.split(':')]

class TestConfig(VersionedConfig):
    val1 = 2.2
    val2 = TestValue()

s = TestConfig.to_json()
TestConfig.from_json(s)
