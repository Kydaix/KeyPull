KeyPull is a command-line utility to extract keybox/keystore data from your Android phone using ADB.

---

## Requirements

* Python 3.10 or newer
* The Android Debug Bridge (`adb`) available on your `$PATH`

## Installation & Usage

Clone the repository and invoke the module directly with Python:

```bash
$ git clone https://github.com/EndowTheGreat/keypull.git
$ cd keypull
$ python -m pykeypull --help
```

By default the script pulls the same well-known locations as the original Go implementation. You can
override the output directory or provide custom device paths:

```bash
$ python -m pykeypull --output extracted /custom/device/path /another/location
```

## Development

Run the unit test suite with:

```bash
$ make test
```

Pull requests and contributions are absolutely welcome—feel free to fork or improve upon the project however you wish.
