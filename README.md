KeyPull is a command-line utility to extract keybox/keystore data from your Android phone

----

## Installation & Usage (Go)
If you already have Go installed, you can simply pull the latest version and install:
```bash
$ go install github.com/EndowTheGreat/keypull/cmd/keypull@latest
```
Or you can build from source:
```bash
$ git clone https://github.com/EndowTheGreat/keypull.git
$ cd keypull
$ make && cd bin
# or: go build -o bin/keypull cmd/keypull/main.go
$ ./keypull
```

## Python Port
A pure Python reimplementation that mirrors the Go tool is available in the `pykeypull/` directory.
Run it with Python 3.10+ after cloning the repository:
```bash
$ python -m pykeypull --help
```
By default the script pulls the same well-known locations as the Go version. You can override the
output directory or provide custom device paths:
```bash
$ python -m pykeypull --output extracted /custom/device/path /another/location
```

## Contributing
Pull requests and contributions are absolutely welcome, feel free to fork or improve upon my work however you wish.
