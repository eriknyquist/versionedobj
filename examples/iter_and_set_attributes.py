from versionedobj import VersionedObject, Serializer

class NestedObject(VersionedObject):
    var1 = 28
    var2 = 99

class TopObject(VersionedObject):
    var1 = 77.7
    var2 = NestedObject()


serializer = Serializer()

# Create object instance, and serialize it
obj = TopObject()
print(serializer.to_json(obj, indent=4))

# Now, set all attributes to 0
for attr_name in obj:
    obj[attr_name] = 0

# Serialize it again
print(serializer.to_json(obj, indent=4))

