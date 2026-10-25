# How to release

Update SMODERP2D version in:

- `smoderp2d/__init__.py`
- `bin/qgis/smoderp2d-plugin/metadata.txt`

Checkout the version:

```
export SMODERP2D_VERSION=<version>

git checkout v$SMODERP2D_VERSION
```

Build the package:

```
pip3 wheel .
```

Upload package to PyPi:

```
python3 -m twine upload smoderp2d-${SMODERP2D_VERSION}-py3-none-any.whl
```

Build QGIS plugin:

```
(cd ./bin/qgis/smoderp2d-plugin/; ./scripts/build_package.sh)
```

Upload `bin/qgis/smoderp2d-plugin/zip_build/smoderp2d_plugin.zip` to
QGIS Plugin repository.
