Object serialization & versioning framework for python 3x
=========================================================

**versionedobj** is a framework for creating complex python objects that can be
serialized/deserialized to and from strings, or dicts, or JSON files.

**versionedobj** also provides a versioning mechanism, to track changes in object
structure across time, and to migrate between different object versions.

See `API documentation <https://eriknyquist.github.io/versionedobj/versionedobj.html>`_

.. contents:: **Table of Contents**

Example-- VersionedObject as a configuration file
-------------------------------------------------

.. code:: python

    from versionedobj import VersionedObject

    class DisplayConfig(VersionedObject):
        display_mode = "windowed"
        resolution = "1920x1080"
        volume = 0.66

    # Populate class attributes to build your object
    class UserConfig(VersionedObject):
        version = "v1.0.0"
        username = "john smith"
        friend_list = ["user1", "user2", "user3"]
        display_config = DisplayConfig() # VersionedObjects can be nested

    # Create an instance of your object (instance attributes will match class attributes,
    # and the initial values will be whatever values you set on the class attributes)
    cfg = UserConfig()

    # Change some values on the object instance
    cfg.display_config.volume = 1.0
    cfg.username = "jane doe"

    # Save object instance to JSON file
    cfg.to_file('user_config.json', indent=4)

    # Load object instance from JSON file
    cfg.from_file('user_config.json')


You can also save/load object data as a JSON string:

.. code:: python

    >>> obj_as_json = cfg.to_json(indent=4) # Serialize to JSON string
    >>> obj_as_json                         # Print JSON string

    {
        "version": "v1.0.0",
        "username": "jane doe",
        "friend_list": [
                "user1",
                "user2",
                "user3"
        ],
        "display_config": {
            "display_mode": "windowed",
            "resolution": "1920x1080",
            "volume": 1.0
        }
    }

    >>> cfg.from_json(obj_as_json)          # Load from JSON string

Or, as a dict:

.. code:: python

    >>> obj_as_dict = cfg.to_dict()   # Serialize to dict
    >>> obj_as_dict                   # Print dict

    {'version': '1.0.0', 'username': 'jane doe', 'friend_list': ['user1', 'user2', 'user3'], 'display_config': {'display_mode': 'windowed', 'resolution': '1920x1080', 'volume': 1.0}}

    >>> cfg.from_dict(obj_as_dict)    # Load from dict

Accessing versioned object instance attributes
----------------------------------------------

When you create an instance of your VersionedObject class, the instance attributes
will be automatically populated to match the class attributes you have created:

.. code:: python

    from versionedobj import VersionedObject

    class AccountInfo(VersionedObject):
        user_name = "john"
        user_id = 11223344

    class Session(VersionedObject):
        ip_addr = "255.255.255.255"
        port = 22
        account_info = AccountInfo()

    session = Session()

    print(session.ip_addr)
    # "255.255.255.255"

    print(session.account_info.user_name)
    # "john"

    session.account_info.user_name = "jane"

    print(session.account_info.user_name)
    # "jane"

Alternatively, you can treat a VersionedObject instance as a dict, and access
attributes by passing their full name as the key:

.. code:: python

    print(session['account_info.user_name'])
    # "jane"

    session['account_info.user_name'] = "jack"

    print(session['account_info.user_name'])
    # "jack"

Iterating over versioned object instance attributes
---------------------------------------------------

If you want to enumerate all attribute names & values on a versioned object instance,
you can use the ``object_attributes()`` method, which returns a generator for all instance
attributes:

.. code:: python

    from versionedobj import VersionedObject

    class AccountInfo(VersionedObject):
        user_name = "john"
        user_id = 11223344

    class Session(VersionedObject):
        ip_addr = "255.255.255.255"
        port = 22
        account_info = AccountInfo()

    session = Session()

    for attr_name, attr_value in session.object_attributes():
        print(f"{attr_name}: {attr_value}")

    # Output looks like this:
    #
    # ip_addr: 255.255.255.255
    # port: 22
    # account_info.user_name: john
    # account_info.user_id: 11223344

Filtering serialization/deserialization output
----------------------------------------------

Whitelisting by field name
**************************

When serializing, if you only want to output certain fields, you can use the 'only'
parameter to specify which fields should be output (effectively a whitelist by field name):

.. code:: python

    cfg.to_file('user_config.json', only=['version', 'username', 'display_config.resolution'])

    # Output looks like this:
    #
    # {
    #     "version": "v1.0.0",
    #     "username": "jane doe",
    #     "display_config": {
    #         "resolution": "1920x1080",
    #     }
    # }

The same parameter can be used for de-serializing:

.. code:: python

    cfg.from_file('user_config.json', only=['display_config.display_mode'])

    # Only the 'display_config.display_mode' field is loaded from the file

Blacklisting by field name
**************************

When serializing, if you *don't* want to output certain fields, you can use the 'ignore'
parameter to specify which fields should be excluded from output (effectively a blacklist
by field name):

.. code:: python

    cfg.to_file('user_config.json', ignore=['friend_list', 'display_config.volume'])

    # Output looks like this:
    #
    # {
    #     "version": "v1.0.0",
    #     "username": "jane doe",
    #     "display_config": {
    #         "display_mode": "windowed",
    #         "resolution": "1920x1080"
    #     }
    # }

The same parameter can be used for de-serializing:

.. code:: python

    cfg.from_file('user_config.json', ignore=['friend_list'])

    # Every field except for the 'friend_list' field is loaded from the file

Migrations: making use of the version number
--------------------------------------------

Any VersionedObject object can have a ``version`` attribute, which can be any object,
although it is typically a string (e.g. ``"v1.2.3"``). This version attribute can be
used to support migrations for older objects, in the event that you need to
change the format of your object.

Example scenario, part 1: you have created a beautiful versioned object
***********************************************************************

Let's take the same config file definition from the previous example:

.. code:: python

    from versionedobj import VersionedObject

    # Nested config object
    class DisplayConfig(VersionedObject):
        display_mode = "windowed"
        resolution = "1920x1080"
        volume = 0.66

    # Top-level config object with another nested config object
    class UserConfig(VersionedObject):
        version = "v1.0.0"
        username = "john smith"
        friend_list = ["user1", "user2", "user3"]
        display_config = DisplayConfig()

Imagine you've already released this code out into the world. People are already
using it, and they have JSON files generated by your ``UserConfig`` class sitting
on their computers.

Example scenario, part 2: you update your software, modifying the versioned object
**********************************************************************************

Now, imagine you are making a new release of your software, and some new features
require you to make the following changes to your versioned object:

* remove the the ``DisplayConfig.resolution`` field entirely
* change the name of ``DisplayConfig.volume`` to ``DisplayConfig.volumes``
* change the value of ``DisplayConfig.volumes`` from a float to a list

.. code:: python

    from versionedobj import VersionedObject

    # Nested config object
    class DisplayConfig(VersionedObject):
        display_mode = "windowed"
        # 'resolution' field is deleted
        volumes = [0.66, 0.1] # 'volume' is now called 'volumes', and is a list

    # Top-level config object with another nested config object
    class UserConfig(VersionedObject):
        version = "v1.0.0"
        username = "john smith"
        friend_list = ["user1", "user2", "user3"]
        display_config = DisplayConfig()

Uh-oh, you have a problem...
****************************

Right now, if you send this updated UserConfig class to your existing users, it will fail
to load their existing JSON files with version ``v1.0.0``, since those files will contain
the ``DisplayConfig.resolution`` field that we deleted in ``v1.0.1``, and
``DisplayConfig.volume`` will similarly be gone, having been replaced with
``DisplayConfig.volumes``. This situation is what migrations are for.

Solution-- migrations!
**********************

The solution is to:

#. Change the version number to something new, e.g. ``v1.0.0`` becomes ``v1.0.1``
#. Write a migration function to transform ``v1.0.0`` object data into ``v1.0.1`` object data

.. code:: python

    from versionedobj import VersionedObject

    # Nested config object
    class DisplayConfig(VersionedObject):
        display_mode = "windowed"
        # 'resolution' field is deleted
        volumes = [0.66, 0.1] # 'volume' is now called 'volumes', and is a list

    # Top-level config object with another nested config object
    class UserConfig(VersionedObject):
        version = "v1.0.1" # Version has been updated to 1.0.1
        username = "john smith"
        friend_list = ["user1", "user2", "user3"]
        display_config = DisplayConfig()

    # Create the migration function for v1.0.0 to v1.0.1
    def migrate_100_to_101(attrs):
        del attrs['display_config']['resolution']        # Delete resolution field
        del attrs['display_config']['volume']            # Delete volume field
        attrs['display_config']['volumes'] = [0.66, 0.1] # Add defaults for new volume values
        return attrs                                     # Return modified data (important!)

    # Add the migration function for v1.0.0 to v1.0.1
    UserConfig.add_migration("v1.0.0", "v1.0.1", migrate_100_to_101)

after you add the migration function and update the version to ``v1.0.1``, JSON files
that are loaded and contain the version ``v1.0.0`` will be automatically migrated to version
``v1.0.1`` using the migration function you added.

The downside to this approach, is that you have to manually udpate the version number,
and write a new migration function, anytime the structure of your config data changes.

The upside, of course, is that you can relatively easily support migrating any older
version of your config file to the current version.

If you don't need the versioning/migration functionality, just never change your version
number, or don't create a ``version`` attribute on your ``VersionedObject`` classes.

Migrations: migrating an unversioned object
-------------------------------------------

You may run into a situation where you release an unversioned object, but then
later you need to make changes, and migrate an unversioned object to a versioned object.

This can be handled simply by passing "None" to the "from_version" parameter to the "add_migration()"
method. For example:

.. code:: python

    UserConfig.add_migration(None, "v1.0.0", migrate_none_to_100)

Validating input data without deserializing
-------------------------------------------

You may want to validate some serialized object data without actually deserializing
and loading the object values. You can use the ``validate_dict`` method for this.

.. code:: python

    from versionedobj import VersionedObject

    class Recipe(VersionedObject):
        ingredient_1 = "onions"
        ingredient_2 = "tomatoes"
        ingredient_3 = "garlic"

    rcp = Recipe()

    rcp.validate_dict({"ingredient_1": "celery", "ingredient_2": "carrots"})
    # Raises versionedobj.exceptions.InputValidationError because 'ingredient_3' is missing

    rcp.validate_dict({"ingredient_1": "celery", "ingredient_2": "carrots", "ingredient_12": "cumin"})
    # Raises versionedobj.exceptions.InputValidationError because 'ingredient_12' is not a valid attribute

Performance/stress test visualization
-------------------------------------

The following image is generated by the ``tests/performance_tests/big_class_performance_test.py`` script,
which creates multiple versioned objects of increasing size.

The time taken to serialize each object to a dict, and also to deserialize the object data
from a dict, and also to create an instance of the object, is measured for each data point in
the graph (Note that measuring the ``from/to_json`` and ``from/to_file`` methods is not very
useful, since we'll just be measuring ``to/from_dict`` with additional JSON parser or file I/O overhead).

Test executed on a system with an Intel Core-i7 running Debian GNU/Linux 10 (buster)
with Linux debian 4.19.0-21-amd64.

.. image:: https://github.com/eriknyquist/versionedobj/raw/master/docs/_images/performance_graph.png

Contributions
-------------

Contributions are welcome, please open a pull request at `<https://github.com/eriknyquist/versionedobj>`_ and ensure that:

#. All existing unit tests pass (run tests via ``python setup.py test``)
#. New unit tests are added to cover any modified/new functionality

If you have any questions about / need help with contributions or unit tests, please
contact Erik at eknyquist@gmail.com.
