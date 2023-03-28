# Conan Extensions
This repository contains extensions for Conan, such as [custom commands](https://docs.conan.io/2/reference/extensions/custom_commands.html)
and [deployers](https://docs.conan.io/2/reference/extensions/deployers.html),
useful for different purposes, like [Artifactory](https://jfrog.com/artifactory) tasks, conan-center-index, etc.

The contents of this repository are *not* production ready, they are intended as an aiding guide,
and you'll probably want to create your own custom commands and/or deployers taking these as a base to ensure they meet your needs.

## Conan config install

To install all the available extensions, run:

```
conan config install https://github.com/conan-io/conan-extensions.git
```

Afterwards, running `conan --help` should show you all the custom commands available.

### Custom Commands

These are the currently supported custom commands:

#### [Convert txt](extensions/commands/migrate/)

Gets a `conanfile.txt` as input and outputs its equivalent `conanfile.py`

```
conan migrate:convert-txt conanfile.txt > conanfile.py
```


#### [List v2 ready](extensions/commands/cci/cmd_list_v2_ready.py)

For a list of references, returns a list of which have their latest revision present in the given remote,
and whether it provides any binaries.

**Parameters**
- **path** _Required_: Path to a folder containing the recipes to be checked.
- **remote** _Required_: Remote repository to check the recipes against.

**Flags**
- **skip-binaries** _Optional_: Do not check if binary packages are available
- **profiles** _Optional_: Profiles to check.

```
conan cci:list-v2-ready conan-center-index/recipes conan-center --profiles profiles
...
....
```

### Testing

To validate a new extension, it's possible to write a test that exercises its usage.
You can use [pytest](https://docs.pytest.org) for testing, producing a stable environment.

```
pytest .
```

We recommend testing with Python 3.6 to respect the [minimum version required](https://github.com/conan-io/tribe/blob/main/design/003-codebase-python.md) for Conan 2.0

### LICENSE

[MIT](LICENSE)
