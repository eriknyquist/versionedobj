from versionedobj import VersionedObject

class NestedObject(VersionedObject):
    var1 = 28
    var2 = 99

class TopObject(VersionedObject):
    var1 = 77.7
    var2 = NestedObject()

# Create object instance, and serialize it
obj = TopObject()
print(obj.to_json(indent=4))

# Now, set all attributes to 0
for attr_name, attr_value in obj.object_attributes():
    obj[attr_name] = 0

# Serialize it again
print(obj.to_json(indent=4))

