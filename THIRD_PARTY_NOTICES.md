# Third-party notices

## Scope

This component and license index accompanies Wewo QA Skills 0.2.0. The project's own source is licensed under [MIT](LICENSE). Third-party components retain their upstream copyrights, licenses and notices; the project license does not replace them.

The self-contained `wewo-qa` artifact executable is built with PyInstaller and includes CPython, application dependencies and collected supporting components. Testers do not need to install these packages. The source requirement ranges below come from `tooling/requirements-dev.txt`; that file is a build input, not a lockfile or a complete inventory of any one executable. Resolved versions and native libraries can differ by operating system, wheel and build environment.

## Python and declared dependencies

Links identify upstream projects or their license documentation. License identifiers describe the package-level terms; incorporated code and wheel-specific notices must also be retained where applicable.

| Component | Declared build input | Purpose | Upstream license |
| --- | --- | --- | --- |
| [CPython](https://docs.python.org/3.12/license.html) | Python 3.12 in the build workflow | Embedded interpreter and standard library | PSF-2.0 and the historical/incorporated-component terms in Python's license documentation. |
| [jsonschema](https://github.com/python-jsonschema/jsonschema) | `>=4.22,<5` | Validate artifact and execution contracts | MIT. |
| [jsonpointer](https://github.com/stefankoegl/python-json-pointer) | `>=3,<4` | Resolve JSON Pointer references | BSD-3-Clause (upstream calls it the Modified BSD License). |
| [openpyxl](https://openpyxl.readthedocs.io/en/stable/) | `>=3.1.5,<4` | Read and write Excel workbooks | MIT. |
| [pypdf](https://github.com/py-pdf/pypdf) | `>=6.0,<7` | Extract PDF source material | BSD-3-Clause. |
| [python-docx](https://github.com/python-openxml/python-docx) | `>=1.2,<2` | Read Word source material | MIT. |
| [python-pptx](https://github.com/scanny/python-pptx) | `>=1.0.2,<2` | Read PowerPoint source material | MIT. |
| [Pillow](https://github.com/python-pillow/Pillow) | `>=11,<13` | Image handling | MIT-CMU; distributed wheels include additional native-library notices. |
| [PyInstaller](https://pyinstaller.org/en/stable/license.html) | `>=6.15,<7` | Build the native executable | GPL-2.0-or-later with the upstream bootloader exception; specified support files use Apache-2.0. |

PyInstaller's exception addresses distribution of applications built with its bootloader. It does not replace the licenses of Python or the packages collected into the executable. The complete build tool is not required on the tester's computer.

## Supporting Python packages

The current dependency graph includes the following supporting packages. Check the exact distributions used for each rebuilt host artifact.

| Component | Use | Upstream license |
| --- | --- | --- |
| [attrs](https://github.com/python-attrs/attrs) | Schema validation support | MIT. |
| [jsonschema-specifications](https://github.com/python-jsonschema/jsonschema-specifications) | JSON Schema vocabulary/specification resources | MIT. |
| [referencing](https://github.com/python-jsonschema/referencing) | Schema reference resolution | MIT. |
| [rpds-py](https://github.com/crate-py/rpds) | Persistent data structures for reference handling | MIT; retain notices supplied with its native distribution. |
| [et_xmlfile](https://pypi.org/project/et-xmlfile/) | XML writing used by openpyxl | MIT. |
| [lxml](https://github.com/lxml/lxml) | XML processing for Office documents | BSD-3-Clause, with additional terms documented in its `LICENSES.txt` and underlying libraries. |
| [typing_extensions](https://github.com/python/typing_extensions) | Python typing compatibility | PSF-2.0. |
| [XlsxWriter](https://github.com/jmcnamara/XlsxWriter) | Dependency of python-pptx | BSD-2-Clause. |

## Additional components observed in the Windows executable

Inspection of the checked-in Windows 0.2.0 executable found the following additional modules. They can be collected through optional imports or packaging hooks when installed in the build environment, even though they are not all declared as direct requirements. This is an observation of that artifact, not a promise that every host build contains the same set.

The inspected executable's SHA-256 is `876f5fb7fc858e59c3157e4ac28331f27406af3f9a4e22e9993d8af78cab49f0`.

| Component | Upstream license / notice source |
| --- | --- |
| [NumPy](https://github.com/numpy/numpy) | BSD-3-Clause and incorporated-component terms. The inspected distribution also declares 0BSD, MIT, Zlib and CC0-1.0; its wheel license includes native numerical-library notices. |
| [cryptography](https://github.com/pyca/cryptography) | Apache-2.0 OR BSD-3-Clause; retain its incorporated-component notices. |
| [CFFI](https://github.com/python-cffi/cffi) | MIT; the `_cffi_backend` extension is present. |
| [Requests](https://github.com/psf/requests) | Apache-2.0; retain upstream `LICENSE` and `NOTICE`. |
| [urllib3](https://github.com/urllib3/urllib3) | MIT. |
| [certifi](https://github.com/certifi/python-certifi) | MPL-2.0, including the supplied certificate bundle terms. |
| [idna](https://github.com/kjd/idna) | BSD-3-Clause. |
| [charset-normalizer](https://github.com/jawah/charset_normalizer) | MIT. |
| [PyYAML](https://github.com/yaml/pyyaml) | MIT. |
| [packaging](https://github.com/pypa/packaging) | Apache-2.0 OR BSD-2-Clause. |
| [setuptools](https://github.com/pypa/setuptools) | MIT; collected vendored modules retain their own licenses. |
| [tomli](https://github.com/hukkin/tomli) | MIT. |
| [pywin32](https://github.com/mhammond/pywin32) | PSF-style license and file-specific notices; selected Windows extensions are present. |

### Native and incorporated components

- **CPython and CFFI:** preserve Python's incorporated-component notices and the terms for collected native libraries. The inspected Windows archive contains OpenSSL 3 and libffi shared libraries. See [OpenSSL licensing](https://openssl-library.org/source/license/) and [libffi's license](https://github.com/libffi/libffi/blob/master/LICENSE).
- **Pillow:** its distributed wheel `LICENSE` contains the PIL/Pillow terms and native-library notices. The inspected build environment's wheel includes notices for Brotli, FreeType, HarfBuzz, Little CMS, libavif, libjpeg-turbo, libpng, libwebp, OpenJPEG, libtiff, XZ and zlib-ng. This software is based in part on the work of the [FreeType Team](https://freetype.org/). The wheel's full notice text, rather than Pillow's top-level identifier alone, describes those components.
- **lxml:** retain its `LICENSE.txt`, `LICENSES.txt`, applicable resource notices and the licenses for the libxml2/libxslt libraries included by the selected wheel. The top-level BSD license does not relicense all incorporated resources.
- **NumPy:** the inspected Windows wheel's `LICENSE.txt` identifies OpenBLAS (BSD-3-Clause), LAPACK (BSD-3-Clause-Open-MPI) and the GCC runtime library (GPL-3.0-or-later WITH GCC-exception-3.1), in addition to the NumPy component notices. Preserve these when distributing that wheel's native libraries.
- **Platform runtime:** Windows builds may include Microsoft C/C++ runtime DLLs; they retain Microsoft's applicable redistribution terms. Other hosts have different platform-library inventories. Do not label all native components MIT merely because this repository uses MIT.

## Build tooling

Build dependencies are distinct from application dependencies, although a package such as `packaging` or `setuptools` can also be collected into a particular executable.

| Component | Upstream license |
| --- | --- |
| [pyinstaller-hooks-contrib](https://github.com/pyinstaller/pyinstaller-hooks-contrib) | Standard hooks/files: GPL-2.0-or-later. Runtime hooks included in generated executables: Apache-2.0. |
| [altgraph](https://github.com/ronaldoussoren/altgraph) | MIT. |
| [packaging](https://github.com/pypa/packaging) | Apache-2.0 OR BSD-2-Clause. |
| [setuptools](https://github.com/pypa/setuptools) | MIT, with separate vendored-component terms. |
| [pefile](https://github.com/erocarrera/pefile) | MIT; Windows build dependency. |
| [pywin32-ctypes](https://github.com/enthought/pywin32-ctypes) | BSD-3-Clause; Windows build dependency. |

## Execution tools and applications

Acceptance-test frameworks, browser binaries, device drivers and language runtimes installed in an independent `qa-automation` workspace are separate from the bundled artifact tool. Their dependency manifests, lockfiles and upstream notices belong with that workspace. Mentioning a runner in a Skill does not mean it is bundled or already available.

The plugin produces `.xmind` and `.xlsx` files; it does not distribute the XMind or Microsoft Office applications. Codex and Claude Code are host products installed separately.

## Maintaining this notice

For each release, review the actual per-host build environment, selected wheels and collected executable contents. Retain the applicable upstream copyright, license, exception and `NOTICE` texts with the distribution; this index and its links do not replace those texts. Optional imports, vendored modules and statically linked libraries need the same review as direct dependencies.

`bin/<host-target>/runtime.json` records the plugin version, source contract and executable hash. It does not record all dependency versions or establish completeness of license files. This document is not a per-build software bill of materials or a certification that every platform's notice inventory has been verified. Recheck the Windows snapshot above whenever that executable changes.
