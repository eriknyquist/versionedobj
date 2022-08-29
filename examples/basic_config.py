from versionedconfig.config import VersionedConfig

# Nested config object
class DisplayConfig(VersionedConfig):
    display_mode = "windowed"
    resolution = "1920x1080"
    volume = 0.66

# Top-level config object with another nested config object
class UserConfig(VersionedConfig):
    version = "1.0.0"
    username = "john smith"
    friend_list = ["user1", "user2", "user3"]
    display_config = DisplayConfig

# Change some values
UserConfig.display_config.volume = 1.0
UserConfig.username = "jane doe"

# Save to JSON file
UserConfig.to_file('user_config.json', indent=4)

# Load from JSON file
UserConfig.from_file('user_config.json')
