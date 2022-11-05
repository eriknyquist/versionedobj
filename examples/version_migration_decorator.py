from versionedobj import VersionedObject, migration, Serializer


# Represents an old version of the object
class OldUserConfig(VersionedObject):
    version = "1.0.0"
    user_name = "jack"
    user_id = 1234
    score = (1001, 18)


# Represents a newer version of the object, where the "user_id" attribute
# was removed, and the value of 'score' was changed to a single integer
class NewUserConfig(VersionedObject):
    version = "1.0.1"
    user_name = "jill"
     # user_id attribute was removed, and 'score' is now
     # just a single integer
    score = 1001


# The new version of the object will need a migration function, to transform 1.0.0
# object data into 1.0.1 object data
@migration(NewUserConfig, "1.0.0", "1.0.1")
def migrate_100_to_101(attrs):
    del attrs["user_id"]  # Delete user_id attr
    attrs["score"] = 1001 # Add new default value for score
    return attrs


# Create instances of the 'new' and 'old' objects
serializer = Serializer()
old_cfg = OldUserConfig()
new_cfg = NewUserConfig()

# Serialize the old object
old_cfg_json = serializer.to_json(old_cfg)

# Load serialized old object data, with new object instance
serializer.from_json(old_cfg_json, new_cfg)

# Success, print loaded object attributes
print(serializer.to_json(new_cfg))
# Output:
# {"version": "1.0.1", "user_name": "jack", "score": 1001}
