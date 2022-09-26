Object serialization & versioning framework for python 3x
=========================================================

.. |tests_badge| image:: https://github.com/eriknyquist/versionedobj/actions/workflows/tests.yml/badge.svg
.. |cov_badge| image:: https://github.com/eriknyquist/versionedobj/actions/workflows/coverage.yml/badge.svg
.. |version_badge| image:: https://badgen.net/pypi/v/versionedobj
.. |license_badge| image:: https://badgen.net/pypi/license/versionedobj

|tests_badge| |cov_badge| |version_badge| |license_badge|

**versionedobj** is a framework for creating complex python objects that can be
serialized/deserialized to and from strings, or dicts, or JSON files.

**versionedobj** also provides a versioning mechanism, to track changes in object
structure across time, and to migrate between different object versions.

See `API documentation <https://eriknyquist.github.io/versionedobj/versionedobj.html>`_

..
    .. only:: html

.. contents:: **Table of Contents**


Installing
----------

Install ``versionedobj`` using pip:

::

    pip install versionedobj

Getting started
---------------

Object definition
*****************

Define objects by creating a new class that inherits from ``VersionedObject``,
and set class attributes to define your object attribubtes:

.. code:: python

    from versionedobj import VersionedObjbect

    class UserConfig(VersionedObject):
        version = "v1.0.0"
        username = "john smith"
        friend_list = ["user1", "user2", "user3"]

You can also nest VersionedObjects by simply assigning another ``VersionedObject``
class or instance object to a class attribute:

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

        # Nested VersionedObjects can be a class object, or an instance of the
        # class, either way will behave the same

        # display_config = DisplayConfig

Creating object instances and accessing object attributes
*********************************************************

The values you set on the class attributes of a ``VersionedObject`` serve as the default
values for that object. When you create an instance of your ``VersionedObject`` class,
instance attributes will automatically be created to match the class attributes, and
the values of the class attributes will be copied over to the instance attributes:

.. code:: python

    obj = UserConfig()

    print(obj.friend_list)
    # Output looks like this: ["user1", "user2", "user3"]

    print(obj.display_config.display_mode)
    # Output looks like this: "windowed"

As well as regular dot notation, you can also treat an object instance like a dict,
and access individual attribubtes using their full dot name as the key:

.. code:: python

    print(obj['friend_list'])
    # Output looks like this: ["user1", "user2", "user3"]

    print(obj['display_config.display_mode'])
    # Output looks like this: "windowed"

    # Change the value of an instance attribute
    obj['display_config.display_mode'] = "fullscreen"

    print(obj['display_config.display_mode'])
    # Output looks like this: "fullscreen"

You can also use the ``object_attributes()`` method to iterate over all object attribute
names and values:

.. code:: python

    for attr_name, attr_value in obj.object_attributes():
        print(f"{attr_name}: {attr_value}")

    # Output looks like this:
    #
    # version: v1.0.0
    # username: john smith
    # friend_list: ["user1", "user2", "user3"]
    # display_config.display_mode: windowed
    # display_config.resolution: 1920x1080
    # display_config.volume: 0.66

Serializing and de-serializing
******************************

Use the ``to_file`` and ``from_file`` methods to serialize/deserialize data to/from a JSON file:

.. code:: python

    # Save object instance to JSON file
    obj.to_file('user_config.json', indent=4)

    # Load object instance from JSON file
    obj.from_file('user_config.json')

You can also save/load object data as a JSON string:

.. code:: python

    # Save object instance to JSON string
    obj_as_json = obj.to_json(indent=4)

    # Load object instance from JSON string
    obj.from_json(obj_as_json)

Or, as a dict:

.. code:: python

    # Save object instance to dict
    obj_as_dict = obj.to_dict()

    # Load object instance from dict
    obj.from_dict(obj_as_dict)

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

A VersionedObject object can have a ``version`` attribute, which can be any object,
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

This can be handled simply by passing "None" to the "add_migration()" method, for the
"from_version" parameter. For example:

.. code:: python

    from versionedobj import VersionedObj

    class UserConfig(VersionedObject):
        version = "v1.1.0"
        username = ""
        friend_list = []

    def migrate_none_to_100(attrs);
        attrs['friend_list'] = [] # Add new 'friend_list' field
        return attrs

    UserConfig.add_migration(None, "v1.0.0", migrate_none_to_100)

Migrations: decorator for migration functions
---------------------------------------------

Instead of calling the ``add_migration()`` class method, you can instead use the
``versionedobj.migration`` decorator on your migration function, if you wish:

.. code:: python

    from versionedobj import VersionedObj, migration

    class UserConfig(VersionedObject):
        version = "v1.0.1"
        username = "john smith"
        friend_list = []

    @migration(UserConfig, "1.0.0", "1.1.0")
    def migrate_100_to_101(attrs);
        attrs['friend_list'] = [] # Add new 'friend_list' field
        return attrs


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

.. image:: https://github.com/eriknyquist/versionedobj/raw/master/images/performance_graph.png

Contributions
-------------

Contributions are welcome, please open a pull request at `<https://github.com/eriknyquist/versionedobj>`_ and ensure that:

#. All existing unit tests pass (run tests via ``python setup.py test``)
#. New unit tests are added to cover any modified/new functionality

If you have any questions about / need help with contributions or unit tests, please
contact Erik at eknyquist@gmail.com.
