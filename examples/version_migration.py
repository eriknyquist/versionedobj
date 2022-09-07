from versionedobj import VersionedObject


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
def migrate_100_to_101(attrs):
    del attrs["user_id"]  # Delete user_id attr
    attrs["score"] = 1001 # Add new default value for score
    return attrs

# Add the migration function the NewUserConfig class
NewUserConfig.add_migration("1.0.0", "1.0.1", migrate_100_to_101)

# Create instances of the 'new' and 'old' objects
old_cfg = OldUserConfig()
new_cfg = NewUserConfig()

# Serialize the old object
old_cfg_json = old_cfg.to_json()

# Load serialized old object data, with new object instance
new_cfg.from_json(old_cfg_json)

# Success, print loaded object attributes
print(new_cfg.to_json())
# Output:
# {"version": "1.0.1", "user_name": "jack", "score": 1001}
