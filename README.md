# Qt Calculator with Docker on Debian 13 and GNOME

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-Qt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Debian](https://img.shields.io/badge/Debian-13-A81D33?style=for-the-badge&logo=debian&logoColor=white)
![GNOME](https://img.shields.io/badge/Desktop-GNOME-4A86CF?style=for-the-badge&logo=gnome&logoColor=white)
![Wayland](https://img.shields.io/badge/Display-Wayland-FFBC00?style=for-the-badge&logo=wayland&logoColor=black)
![X11](https://img.shields.io/badge/Protocol-X11-F28834?style=for-the-badge&logo=xdotorg&logoColor=white)

# Project Overview

This document provides an overview of the project and explains how its files work together to run a Qt graphical application inside a Docker container and display it on the Debian host desktop.

For a detailed, line-by-line explanation of each file, see the dedicated documentation:

- [`README_calculator.md`](README_calculator.md) → `app/calculator.py`
- [`README-Dockerfile.md`](README-Dockerfile.md) → `Dockerfile`
- [`README-docker-compose.md`](README-docker-compose.md) → `docker-compose.yml`
- [`README-calc.md`](README-calc.md) → `calc` script

---

## Purpose

This project is a calculator running inside a Docker container. Its Python environment, PySide6 installation, and software dependencies are contained within the Docker image. However, the application still relies on the Linux host’s X11 display system to show its Qt interface.

**This project is intended primarily as a Docker learning exercise on Linux.** Although the application itself is containerized, its PySide6 interface requires access to the host’s X11 or XWayland display system. It is therefore **not directly portable to Windows or macOS** in its current form.

**It is a practical example of how to run a graphical Python/PySide6 application inside a Docker container and display it through X11 on a Linux desktop.**

The project was developed and tested on **Debian 13 with GNOME running under Wayland**. In this environment, the container communicates through the X11 protocol, while XWayland provides compatibility between the X11 application and the Wayland desktop:

```text
PySide6 container → X11 protocol → XWayland → GNOME/Wayland → screen
```

Other Linux desktop distributions may also work if they provide X11 or XWayland access, but they have not been tested.

---

## 1. The Main Challenge: Displaying a Window from a Container

A Docker container is normally isolated from the rest of the system—this is one of the main purposes of containerization. However, a Qt application needs access to a **display server** to draw and display a window.

On the tested Debian 13 system, GNOME uses Wayland, while XWayland provides compatibility for applications communicating through the X11 protocol.

The main challenge of this project is therefore not Qt itself. It is creating a controlled bridge between the isolated container and the host’s X11-compatible display system. Without this bridge, the application cannot open its window.

This connection relies on three elements configured across several files:

| Element               | Location                                        | Purpose                                                  |
| --------------------- | ----------------------------------------------- | -------------------------------------------------------- |
| Authorization         | `xhost +local:docker` in `calc`                 | Allows the required local connection to the X server     |
| Display address       | `DISPLAY=${DISPLAY}` in `docker-compose.yml`    | Tells the application which X display to use             |
| Communication channel | `/tmp/.X11-unix` volume in `docker-compose.yml` | Gives the container access to the host’s X11 Unix socket |

All three elements must be available for the window to appear.

---

## 2. Project Structure

```text
calculatrice/
├── app/
│   └── calculator.py        → application code (logic and Qt interface)
├── Dockerfile               → instructions used to build the image
├── docker-compose.yml       → runtime configuration (X11, environment, volumes)
├── requirements.txt         → Python dependencies (PySide6)
├── calc                     → system command to install in /usr/local/bin
├── run.sh / stop.sh         → alternative manual start and stop scripts
└── README*.md               → documentation
```

---

## 3. The Application: `app/calculator.py`

A `Calculator` class, derived from `QWidget`, builds the user interface, including the display and button grid. It also manages the calculator’s state through a single variable: `self.expression`.

This variable contains the current mathematical expression as a string, for example:

```python
"12+5"
```

Each button click calls `_on_click(label)`. This method updates `self.expression` according to the selected button—a digit, an operator, `C`, `⌫`, or `=`—and then refreshes the display.

The calculation itself uses `eval()`. Before the expression is evaluated, a character allowlist restricts the accepted input. This reduces the risk of arbitrary code execution within the calculator’s intended use, although `eval()` should still not be considered a general-purpose secure expression parser.

The application starts through `main()`, which:

1. Creates a `QApplication`.
2. Creates and displays the calculator window.
3. Starts the Qt event loop with `app.exec()`.

The program remains inside this event loop until the user closes the window.

*For a complete explanation, see `README_calculator.md`.*

---

## 4. Building the Image: `Dockerfile`

The Dockerfile starts from the lightweight `python:3.12-slim` image and then performs the following steps:

1. Installs the system libraries required by Qt to communicate with X11 and render the interface, including `libgl1`, `libglib2.0-0`, and the required `libxcb-*` libraries. These libraries are not included in the `slim` image by default.
2. Installs PySide6 with `pip` using `requirements.txt`.
3. Copies the application source code from `app/` into the image.
4. Defines the startup command: `python calculator.py`.

The order of these instructions is designed to take advantage of Docker’s build cache. Layers that change infrequently, such as system and Python dependencies, are created before the application source code, which is more likely to change.

This reduces build time when only the Python code has been modified.

*For a complete explanation, see `README-Dockerfile.md`.*

---

## 5. Runtime Configuration: `docker-compose.yml`

The Compose file describes how Docker must build and start the container:

* `build: .` tells Docker Compose to build the image from the Dockerfile in the current project directory.
* `image: qt-calculator` assigns the name `qt-calculator` to the resulting image.
* `environment` passes the host’s `DISPLAY` value to the container.
* `QT_X11_NO_MITSHM=1` disables the MIT-SHM extension for Qt, avoiding potential shared-memory compatibility problems between the container and the host.
* `volumes` mounts the host’s `/tmp/.X11-unix` socket directory inside the container, providing the actual communication channel to X11 or XWayland.
* `network_mode: host` makes the container use the host’s network stack. It is part of this project’s configuration, although the local X11 connection itself primarily relies on `DISPLAY` and the mounted Unix socket.

*For a complete explanation, see `README-docker-compose.md`.*

---

## 6. The User Command: `calc`

The `calc` script is installed as `/usr/local/bin/calc`.

Because `/usr/local/bin` is included in Debian’s default `$PATH`, the command can be executed from any directory.

The script manages the complete calculator lifecycle with a single command:

1. `xhost +local:docker` grants the required local access to the X server.
2. `docker compose ... up -d --build` builds the image when necessary and starts the container **in the background**. The `-d` option immediately returns control of the terminal to the user.
3. A detached subprocess, created with `( ... ) & disown`, waits silently for the container to stop by using `docker wait`.
4. As soon as the calculator window is closed and the container stops, the subprocess automatically revokes the X11 authorization with `xhost -local:docker`.
5. Because the subprocess is detached with `disown`, it can continue running even if the original terminal is closed.

This mechanism removes the need for the user to enter a separate stop command. Opening and closing the calculator window is enough, while the X11 permission is granted and revoked automatically.

*For a complete explanation, see `README-calc.md`.*

---

## 7. `run.sh` and `stop.sh` — Manual Alternative

These scripts provide an earlier or alternative way to manage the application manually from the project directory.

Because they are executed directly from that directory, they do not need the `--project-directory` option: Docker Compose automatically finds `docker-compose.yml` in the current directory.

* `run.sh` grants X11 access and starts the container in the background.
* `stop.sh` stops and removes the container with `docker compose down`, then revokes X11 access.

Unlike `calc`, this method does not revoke X11 access automatically when the calculator window is closed.

The user must explicitly run:

```bash
./stop.sh
```

Closing the calculator window stops the container, but without running `stop.sh`, the X11 authorization granted by `run.sh` remains active.

---

## 8. Complete Workflow: From the `calc` Command to the Screen

```text
Terminal: calc
   │
   ├─► xhost +local:docker
   │       Grants the required X11 access
   │
   ├─► docker compose up -d --build
   │       Builds the image when necessary and starts the container
   │         │
   │         ├─► Dockerfile processed
   │         │       Creates or updates the "qt-calculator" image
   │         │
   │         └─► Container starts and runs `python calculator.py`
   │                   │
   │                   ├─► QApplication is created
   │                   ├─► Calculator window is displayed
   │                   │       Through DISPLAY and the mounted X11 socket
   │                   │       Authorized by the previous xhost command
   │                   └─► Qt event loop handles input, clicks, and calculations
   │
   ├─► Background process: docker wait <container_id>
   │       Waits silently while the calculator remains open
   │
   └─► "Calculator started."
           The terminal is immediately available again


   [ ... the user operates the calculator ... ]


Calculator window closed
   │
   └─► Container stops
             │
             └─► docker wait returns
                       │
                       └─► xhost -local:docker
                               Revokes the X11 authorization automatically
```

---

## Summary

This project demonstrates how three distinct layers work together:

1. **A standard graphical application** written with Qt/PySide6, which does not need to know that it is running inside Docker.
2. **A containerized environment**, defined by the Dockerfile and Docker Compose, which packages the application with its Python and system dependencies.
3. **An explicit bridge to the host display**, based on X11 authorization, the `DISPLAY` environment variable, and the `/tmp/.X11-unix` socket.

On the tested Debian 13 GNOME system, the container uses the X11 protocol and XWayland displays the resulting window within the Wayland desktop session.

The `calc` script completes the workflow by making the container easy to use: one command starts the application, and simply closing the calculator window stops the container and automatically revokes the temporary X11 authorization.

---

## Acknowledgements

## Acknowledgements

The documentation was written, reviewed, and technically refined with the assistance of ChatGPT by OpenAI. The final content was checked and approved by the project author.

