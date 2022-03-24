# Bus Pirate helper tool for UART monitoring

- Connects to a [Bus Pirate](https://www.sparkfun.com/products/12942) via [pyserial](https://github.com/pyserial/pyserial)
  - Tries to auto-detect the pirate based on USB vendor & product ids
- Send binary commands to put it into UART mode, hardcoded to 115200 baud and (HiZ, 8/N/1, RX idle high)
  - these values work well with the [esphome logger](https://esphome.io/components/logger.html) defaults
- read from UART and display on computer's terminal
  - TX is blocked

The purpose is to give me a single command for esphome log viewing, and it may end up being useful for other things.

The `MISO` pin of the Bus Pirate should be connected to the TX pin of the device to monitor, and the Grounds should also be connected.

I have v5.10 of the bus pirate firmware running on my v3 hardware.

## Running

```
bp_monitor
```

This is the base command. It will attempt to auto-select the Bus Pirate. If needed, it'll prompt the user to choose a serial port, or it can be specified on the command line with `-p` or `--port`.

## Installation

AFAICT, [pipx](https://pypa.github.io/pipx/) is the "right" way to install python-based executables. I have not "published" this code, so use one of the [PACKAGE_SPEC](https://pypa.github.io/pipx/docs/#pipx-install) options that does not rely on that.

```
pipx install [--editable] LOCAL_PATH
pipx install git+https://github.com/e28eta/buspirate-uart-monitor
```

I've used `--editable` so that updates to the local git repo are immediately reflected in the executable