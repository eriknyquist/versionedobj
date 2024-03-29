from versionedobj import VersionedObject, Serializer, ListField

# The list will contain objects of this type only
class UserData(VersionedObject):
    name = "john"
    age = 30

# This object will contain a list of multiple users
class AllUserData(VersionedObject):
    # a ListField may only contain instances of the same class
    users = ListField(UserData)

all_user_data = AllUserData()
serializer = Serializer()

# Add some users to the list
all_user_data.users.append(UserData(initial_values={'name': 'sam', 'age': 66}))
all_user_data.users.append(UserData(initial_values={'name': 'sally', 'age': 28}))

# Serialize object and print out JSON data
json_str = serializer.to_json(all_user_data, indent=4)
print(json_str)

# Create new instance of user data object, without any users added
other_user_data = AllUserData()

# Load new object from JSON string containing the added users and print user list
serializer.from_json(json_str, other_user_data)
print(other_user_data.users)
