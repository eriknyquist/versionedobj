from versionedobj import VersionedObject

class AccountInfo(VersionedObject):
    user_name = "john"
    user_id = 11223344

class Session(VersionedObject):
    ip_addr = "255.255.255.255"
    port = 22
    account_info = AccountInfo()

session = Session()

for attr_name, attr_value in session:
    print(f"{attr_name}: {attr_value}")
