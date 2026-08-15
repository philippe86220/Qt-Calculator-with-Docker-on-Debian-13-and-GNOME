# README — `Dockerfile` Explained Line by Line

This document provides a detailed explanation of how the calculator’s Docker image is built.

---

**Line 1**

```dockerfile
FROM python:3.12-slim
```

This defines the base image: Python 3.12 running on a lightweight Debian variant called `slim`.

The image contains the Python interpreter and a minimal set of system packages. It is significantly smaller than a complete Debian image, but graphical libraries are intentionally omitted. This is why the libraries required by Qt must be installed manually later in the Dockerfile.

---

**Line 3**

```dockerfile
# Dépendances système nécessaires pour Qt (PySide6) en environnement graphique X11
```

This is a comment and is ignored by Docker. It documents the purpose of the following `RUN` instruction.

In English, the comment could be written as:

```dockerfile
# System dependencies required by Qt (PySide6) in an X11 graphical environment
```

---

## Lines 4–22 — Installing the System Libraries

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libegl1 \
    libglib2.0-0 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xinerama0 \
    libfontconfig1 \
    libxrender1 \
    libxi6 \
    && rm -rf /var/lib/apt/lists/*
```

This is a single `RUN` instruction split across several physical lines using `\`.

The backslash escapes the newline, allowing the shell command to continue on the following line. Without it, each line would be interpreted separately and the instruction would not work as intended.

* `apt-get update` refreshes the list of packages available from the Debian repositories.
* `&&` executes the next command only if the preceding command succeeds. This prevents Docker from attempting an installation with an unavailable or outdated package index if `apt-get update` fails.
* `apt-get install -y` installs the packages without asking for confirmation.

  * `-y` automatically answers “yes” to installation prompts.
  * This is required in a non-interactive Docker build.
* `--no-install-recommends` installs the explicitly requested packages and their required dependencies, without automatically installing Debian’s additional recommended packages. This helps keep the image smaller.

The listed packages provide the shared libraries, generally stored as `.so` files, required by PySide6 and Qt:

* `libgl1` and `libegl1`: provide OpenGL and EGL graphics support.
* `libglib2.0-0`: provides low-level runtime facilities required by some Qt components and graphical integrations. This was the missing library during the first build attempt.
* `libxkbcommon0` and `libxkbcommon-x11-0`: provide keyboard layout and keymap handling.
* `libdbus-1-3`: provides the D-Bus inter-process communication system commonly used by Linux desktop environments.
* `libxcb-*`: provide XCB libraries and extensions. XCB is a low-level interface to the X11 protocol used by Qt’s X11 platform integration.
* `libfontconfig1`: provides font discovery and configuration.
* `libxrender1`: provides support for the X Rendering Extension used for 2D rendering.
* `libxi6`: provides support for input devices, such as the mouse and keyboard, through the X11 Input Extension.

The final part of the instruction is:

```dockerfile
&& rm -rf /var/lib/apt/lists/*
```

This removes the downloaded APT package lists after the packages have been installed.

The cleanup is performed inside the same `RUN` instruction as `apt-get update` and `apt-get install`. This is important because each `RUN` instruction creates an immutable Docker image layer.

If the package lists were created in one layer and removed only in a later layer, the files would disappear from the visible filesystem but their data would still exist in the earlier image layer. Removing them within the same instruction therefore reduces the final image size effectively.

---

**Line 24**

```dockerfile
WORKDIR /app
```

This sets `/app` as the current working directory inside the image and, later, inside the running container.

The following instructions and commands, including `COPY`, `RUN`, and `CMD`, use this directory as their working location.

Docker automatically creates `/app` if it does not already exist.

---

**Line 26**

```dockerfile
COPY requirements.txt .
```

This copies `requirements.txt` from the Docker build context into `/app/` inside the image.

The destination `.` refers to the current working directory defined by:

```dockerfile
WORKDIR /app
```

The resulting path inside the image is therefore:

```text
/app/requirements.txt
```

---

**Line 27**

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

This installs the Python dependencies listed in `requirements.txt`, which currently contains PySide6.

* `-r requirements.txt` tells `pip` to read the package list from the specified file.
* `--no-cache-dir` prevents `pip` from keeping a local cache of the downloaded installation packages.

The cache is not required inside the final image, so disabling it saves disk space.

---

## Why Is `requirements.txt` Copied Before the Application Code?

This instruction:

```dockerfile
COPY requirements.txt .
```

appears before:

```dockerfile
COPY app/ .
```

This order is a Docker build-cache optimization.

Each Dockerfile instruction creates a layer that Docker can cache and reuse during future builds.

If only `calculator.py` is modified while `requirements.txt` remains unchanged, Docker can reuse the existing cached layer created by:

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

There is no need to download and reinstall PySide6.

This corresponds to the `CACHED` status displayed by Docker during subsequent builds.

If `requirements.txt` and the application source code were copied together, every change to `calculator.py` would invalidate the copy layer and all the following layers. Docker would then run `pip install` again unnecessarily.

Separating the dependency file from the source code therefore makes repeated builds faster.

---

**Line 29**

```dockerfile
COPY app/ .
```

This copies the entire contents of the `app/` directory from the Docker build context into `/app/` inside the image.

In this project, it copies:

```text
app/calculator.py
```

to:

```text
/app/calculator.py
```

Because this instruction appears after the dependency installation, changes to the application code do not invalidate the previously cached dependency layers.

---

**Line 31**

```dockerfile
CMD ["python", "calculator.py"]
```

This defines the command executed by default when a container is started from the image, unless another command is explicitly provided at runtime.

The command starts the calculator with:

```bash
python calculator.py
```

The Dockerfile uses the JSON array syntax, also called the **exec form**, rather than the shell form:

```dockerfile
CMD python calculator.py
```

The exec form is recommended because Docker starts the Python process directly without placing an intermediate `/bin/sh -c` shell in front of it.

This allows the application to receive operating-system signals more directly, including the signal sent when Docker stops the container. It therefore helps the application shut down cleanly.

---

## Build Process Summary

1. Start from a lightweight Python base image.
2. Install the system libraries required by Qt, X11, and graphical rendering.
3. Install the Python dependencies, including PySide6.
4. Copy the application source code into the image.
5. Define the command used to start the calculator.

Docker caches each step independently.

The instructions are deliberately ordered so that the most stable layers—the system libraries and Python dependencies—are created before the application source code, which is more likely to change.

As a result, Docker can reuse the expensive dependency layers and rebuild only the final source-code layer when `calculator.py` is modified.
