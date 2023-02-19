Object serialization & versioning framework for python 3x
=========================================================

.. |tests_badge| image:: https://github.com/eriknyquist/versionedobj/actions/workflows/tests.yml/badge.svg
.. |cov_badge| image:: https://github.com/eriknyquist/versionedobj/actions/workflows/coverage.yml/badge.svg
.. |version_badge| image:: https://badgen.net/pypi/v/versionedobj
.. |license_badge| image:: https://badgen.net/pypi/license/versionedobj
.. |codeclimate_badge| image:: https://api.codeclimate.com/v1/badges/77e77f051600a584019a/maintainability

|tests_badge| |cov_badge| |codeclimate_badge| |version_badge| |license_badge|

**versionedobj** is an object serialization framework that allows you to create
complex python objects that can be serialized/deserialized to and from strings,
or dicts, or JSON files.

**versionedobj** also provides a versioning mechanism, to track changes in object
structure across time, and to migrate between different object versions.

See `API documentation <https://eriknyquist.github.io/versionedobj/versionedobj.html>`_

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
and set class attributes to define your object attributes:

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
and access individual attributes using their full dot name as the key:

.. code:: python

    print(obj['friend_list'])
    # Output looks like this: ["user1", "user2", "user3"]

    print(obj['display_config.display_mode'])
    # Output looks like this: "windowed"

    # Change the value of an instance attribute
    obj['display_config.display_mode'] = "fullscreen"

    print(obj['display_config.display_mode'])
    # Output looks like this: "fullscreen"

You can also treat a ``VersionedObjbect`` instance as an iterable, to iterate
over all object attribute names, as you would with keys in a dict:

.. code:: python

    for attr_name in obj:
        print(f"{attr_name}: {obj[attr_name]}")

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

Create an instance of the ``versionedobj.Serializer`` class, and use the ``to_file``
and ``from_file`` methods to serialize/deserialize data to/from a JSON file:

.. code:: python

    from versionedobj import VersionedObject, Serializer

    class DisplayConfig(VersionedObject):
        display_mode = "windowed"
        resolution = "1920x1080"
        volume = 0.66

    class UserConfig(VersionedObject):
        version = "v1.0.0"
        username = "john smith"
        friend_list = ["user1", "user2", "user3"]
        display_config = DisplayConfig() # VersionedObjects can be nested

    # Create an instance of our VersionedObject
    obj = UserConfig()

    # Create a serializer instance
    serializer = Serializer(obj)

    # Save object instance to JSON file
    serializer.to_file('user_config.json', indent=4)

    # Load JSON file and populate the same object instance
    serializer.from_file('user_config.json')

You can also save/load object data as a JSON string:

.. code:: python

    # Save object instance to JSON string
    obj_as_json = serializer.to_json(indent=4)

    # Load object instance from JSON string
    serializer.from_json(obj_as_json)

Or, as a dict:

.. code:: python

    # Save object instance to dict
    obj_as_dict = serializer.to_dict()

    # Load object instance from dict
    serializer.from_dict(obj_as_dict)

Using one Serializer instance with multiple object types
--------------------------------------------------------

For convenience, you can pass an object instance when you create a ``versionedobj.Serializer``,
and this object will be used for all future serialization/deserialization operations,
so that you don't have to pass in the object instance every time (as shown in previous
examples).

However, this is not required, and you can optionally provide an object instance
for all serialization/deserialization methods, if you want to (for example) use
a single ``versionedobj.Serializer`` instance for multiple object types:

.. code:: python

    from versionedobj import VersionedObject, Serializer

    class ObjectA(VersionedObject):
        name = "john"
        age = 44

    class ObjectB(VersionedObject):
        last_login_time = 12345678
        enabled = False

    # Create an instance of each object
    a = ObjectA()
    b = ObjectB()
    serializer = Serializer()

    # Serialize both objects using the same serializer
    a_jsonstr = serializer.to_json(a)
    b_jsonstr = serializer.to_json(b)

    # De-serialize both objects using the same serializer
    serializer.from_json(a_jsonstr, a)
    serializer.from_json(b_jsonstr, b)

Filtering serialization/deserialization output
----------------------------------------------

Whitelisting by field name
**************************

When serializing, if you only want to output certain fields, you can use the 'only'
parameter to specify which fields should be output (effectively a whitelist by field name):

.. code:: python

    serializer.to_file('user_config.json', only=['version', 'username', 'display_config.resolution'])

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

    serializer.from_file('user_config.json', only=['display_config.display_mode'])

    # Only the 'display_config.display_mode' field is loaded from the file

Blacklisting by field name
**************************

When serializing, if you *don't* want to output certain fields, you can use the 'ignore'
parameter to specify which fields should be excluded from output (effectively a blacklist
by field name):

.. code:: python

    serializer.to_file('user_config.json', ignore=['friend_list', 'display_config.volume'])

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

    serializer.from_file('user_config.json', ignore=['friend_list'])

    # Every field except for the 'friend_list' field is loaded from the file

versionedobj.ListField: store a sequence of objects in a single field
---------------------------------------------------------------------

``versionedobj.ListField`` is a list class that behaves exactly like a regular python list,
except for the following 2 differences:

* Only instances of a class which is a subclass of the ``VersionedObject`` may be added to lists
  (ValueError is raised otherwise)
* Only instances of the same class may be added to a single list (ValueError is raised otherwise)

You can assign a ``versionedobj.ListField`` instance as the value for a field in your versioned object
class definition, and that field can then hold a sequence of multiple versioned objects. This
is useful if you need to store a variably-sized collection of objects that are created a runtime.

.. code:: python

    from versionedobj import VersionedObject, Serializer, ListField

    # The list will contain objects of this type only
    class UserData(VersionedObject):
        name = "john"
        age = 30

    # This object will contain a list of multiple users
    class AllUserData(VersionedObject):
        # a List may only contain instances of the same class
        users = ListField(UserData)

    all_user_data = AllUserData()

    # Add some users to the list
    all_user_data.users.append(UserData(initial_values={'name': 'sam', 'age': 66}))
    all_user_data.users.append(UserData(initial_values={'name': 'sally', 'age': 28}))

    # Serialize object and print out JSON data
    print(Serializer(all_user_data).to_json(indent=4))

    # Output looks like this:
    #
    # {
    #     "users": [
    #         {
    #             "name": "sam",
    #             "age": 66
    #         },
    #         {
    #             "name": "sally",
    #             "age": 28
    #         }
    #     ]
    # }

Context manager for loading & editing saved object data
-------------------------------------------------------

If you want to load object data from a JSON file, make some changes to the data,
and save it back to the same JSON file, then you can use the ``FileLoader`` context
manager, which will load/create the file for you on entry, return a deserialized
object for you to modify, and then serializes your modified object back to the same
file on exit. This may be useful if you are worried about forgetting to re-serialize
the object when you are done.

.. code:: python

    from versionedobj import VersionedObject, FileLoader

    class Recipe(VersionedObject):
        ingredient_1 = "onions"
        ingredient_2 = "tomatoes"
        ingredient_3 = "garlic"

    # Creates a new instance of the object, and loads data from
    # "recipe.json" if the file already exists
    with FileLoader(Recipe, "recipe.json") as obj:
        # Change something
        obj.ingredient_3 = "celery"

    # recipe.json now looks like this:
    #
    # {
    #     "ingredient_1": "onions",
    #     "ingredient_2": "tomatoes",
    #     "ingredient_3": "celery",
    # }

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
#. Use the ``versionedobj.migration`` decorator to register your migration function

.. code:: python

    from versionedobj import VersionedObject, migration

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
    @migration(UserConfig, "v1.0.0", "v1.0.1")
    def migrate_100_to_101(attrs):
        del attrs['display_config']['resolution']        # Delete resolution field
        del attrs['display_config']['volume']            # Delete volume field
        attrs['display_config']['volumes'] = [0.66, 0.1] # Add defaults for new volume values
        return attrs                                     # Return modified data (important!)

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

    from versionedobj import VersionedObj, migration

    class UserConfig(VersionedObject):
        version = "v1.0.0"
        username = ""
        friend_list = []

    @migration(UserConfig, None, "v1.0.0")
    def migrate_none_to_100(attrs);
        attrs['friend_list'] = [] # Add new 'friend_list' field
        return attrs


Validating input data without deserializing
-------------------------------------------

You may want to validate some serialized object data without actually deserializing
and loading the object values. You can use the ``Serializer.validate_dict`` method for this.

.. code:: python

    from versionedobj import VersionedObject, Serializer

    class Recipe(VersionedObject):
        ingredient_1 = "onions"
        ingredient_2 = "tomatoes"
        ingredient_3 = "garlic"

    rcp = Recipe()
    serializer = Serializer(rcp)

    serializer.validate_dict({"ingredient_1": "celery", "ingredient_2": "carrots"})
    # Raises versionedobj.exceptions.InputValidationError because 'ingredient_3' is missing

    serializer.validate_dict({"ingredient_1": "celery", "ingredient_2": "carrots", "ingredient_12": "cumin"})
    # Raises versionedobj.exceptions.InputValidationError because 'ingredient_12' is not a valid attribute

Resetting object instance to default values
-------------------------------------------

You can use the ``Serializer.reset_to_defaults`` method to set all instance attributes to
the default values defined in the matching class attributes.

.. code:: python

    from versionedobj import VersionedObject, Serializer

    class Recipe(VersionedObject):
        ingredient_1 = "onions"
        ingredient_2 = "tomatoes"
        ingredient_3 = "garlic"

    rcp = Recipe()
    serializer = Serializer(rcp)

    # Change a value
    rcp.ingredient_1 = "celery"

    print(serializer.to_dict())
    # {"ingredient_1": "celery", "ingredient_2": "tomatoes", "ingredient_3": "garlic"}

    # Reset object instance to defaults
    serializer.reset_to_defaults()

    print(serializer.to_dict())
    # {"ingredient_1": "onions", "ingredient_2": "tomatoes", "ingredient_3": "garlic"}

Testing object instance equality
--------------------------------

You can test whether two ``VersionedObject`` instances are equal in both structure and
values, the same way in which you would check equality of any other two objects:

.. code:: python

    from versionedobj import VersionedObject

    class Recipe(VersionedObject):
        ingredient_1 = "onions"
        ingredient_2 = "tomatoes"
        ingredient_3 = "garlic"

    rcp1 = Recipe()
    rcp2 = Recipe()

    print(rcp1 == rcp2)
    # True

    rcp1.ingredient_3 = "ginger"

    print(rcp1 == rcp2)
    # False

In order for two ``VersionedObject`` instances to be considered equal, the following
conditions must be true:

* Both objects are instances of the same class
* Both objects contain matching attribute names and values

Object instance hashing
-----------------------

Objects can be uniquely hashed based on their instance attribute values, using the builtin
``hash()`` function. This means, for example, that you can use object instances as dict keys:

.. code:: python

    from versionedobj import VersionedObject

    class Person(VersionedObject):
        name = "sam"
        age = 31

    p1 = Person()
    p2 = Person()

    # Change 1 value on p2 so the hash value is different
    p2.age = 32

    d = {p1: "a", p2: "b"}
    print(d)
    # { Person({"name": "sam", "age": 31}): "a", Person({"name": "sam", "age": 32}): "b" }

Testing whether object instances contain specific values
--------------------------------------------------------

You can check whether an object instance contains a particular attribute value using the ``in``
keyword:

.. code:: python

    from versionedobj import VersionedObject

    class Person(VersionedObject):
        name = "sam"
        age = 31

    p = Person()

    print("sam" in p)
    # True

    p.name = "sally"

    print("sam" in p)
    # False

    print("sally" in p)
    # True

Performance/stress test visualization
-------------------------------------

The following image is generated by the ``tests/performance_tests/big_class_performance_test.py`` script,
which creates and serializes/deserializes multiple versioned objects of an incrementally increasing size,
and simultaneously having an increasing depth of contained nested objects.

Each data point in the graph represents measurements taken for an object of a particular size.
The time taken to serialize the object to a dict, and also to deserialize the object data
from a dict, and also to create an instance of the object, is measured for each object size. It is
worth mentioning that measuring the ``from/to_json`` and ``from/to_file`` methods is not very
useful in this case, since that would only be measuring ``to/from_dict`` with additional JSON
parser or file I/O overhead. That is why this graph only measures ``to/from_dict``.

This test was executed on a system with an Intel Core-i7 running Debian GNU/Linux 10 (buster)
with Linux debian 4.19.0-21-amd64.

.. image:: https://github.com/eriknyquist/versionedobj/raw/master/images/performance_graph.png

Contributions
-------------

Contributions are welcome, please open a pull request at `<https://github.com/eriknyquist/versionedobj>`_ and ensure that:

#. All existing unit tests pass (run tests via ``python setup.py test``)
#. New unit tests are added to cover any modified/new functionality (run ``python code_coverage.py``
   to ensure that coverage is above 98%)

You will need to install packages required for development, these are listed in ``dev_requirements.txt``:

::

    pip install -r dev_requirements.txt

If you have any questions about / need help with contributions or unit tests, please
contact Erik at eknyquist@gmail.com.
