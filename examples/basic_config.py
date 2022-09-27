from versionedobj import VersionedObject, Serializer

# Nested config object
class DisplayConfig(VersionedObject):
    display_mode = "windowed"
    resolution = "1920x1080"
    volume = 0.66

# Top-level config object with another nested config object
class UserConfig(VersionedObject):
    version = "1.0.0"
    username = "john smith"
    friend_list = ["user1", "user2", "user3"]
    display_config = DisplayConfig()


s = Serializer()

# Create an instance of the top-level object
cfg = UserConfig()

# Change some values
cfg.display_config.volume = 1.0
cfg.username = "jane doe"

# Save to JSON file
s.to_file(cfg, 'user_config.json', indent=4)

# Load from JSON file
s.from_file(cfg, 'user_config.json')

print(s.to_dict(cfg))
