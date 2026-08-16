# README — The `calc` Script Explained Line by Line

This document provides a detailed explanation of the `calc` command installed in `/usr/local/bin`.

The script starts the calculator container in the background and automatically revokes the temporary X11 authorization when the calculator window is closed.

---

**Line 1**

```bash
#!/bin/bash
```

This is the shebang. It tells the operating system that the script must be interpreted by Bash.

The interpreter must be specified using a valid path. In this case, Bash is located at:

```text
/bin/bash
```

The initial `/` is important because it makes the path absolute.

The shebang allows the script to be executed directly:

```bash
calc
```

instead of explicitly invoking Bash:

```bash
bash /usr/local/bin/calc
```

Another commonly used form would be:

```bash
#!/usr/bin/env bash
```

but this project deliberately uses the direct `/bin/bash` path.

---

**Line 2**

```bash
set -e
```

This tells Bash to stop the script when a command returns a non-zero exit status.

It prevents the script from continuing after certain failures. For example, if the initial `xhost` command fails, the script should not proceed as though access to the display server had been granted successfully.

However, `set -e` is not a complete error-management system. Its exact behavior depends on the shell context, particularly inside conditionals, command substitutions, and compound commands.

In this script, it provides a useful first level of protection against continuing after an error.

---

**Line 4**

```bash
xhost +local:docker
```

This modifies the access-control list of the host’s X server so that the container can establish the required local X11 connection.

Without a suitable authorization, the container could have the correct `DISPLAY` variable and access to `/tmp/.X11-unix`, but the X server could still reject the connection.

An important technical detail is that `docker` is not authenticated here as a unique application identity.

With the `local` connection family, this command grants access more broadly to local non-network connections accepted by the X server. It is therefore advisable to keep this authorization active only for as long as it is needed.

The script later removes it with:

```bash
xhost -local:docker
```

On the tested Debian 13 GNOME system, this permission applies to the XWayland compatibility server used by the Wayland desktop session.

---

**Line 5**

```bash
docker compose --project-directory /home/philippe86220/Documents/docker/calculatrice up -d --build
```

This command builds and starts the calculator service.

### `--project-directory`

```bash
--project-directory /home/philippe86220/Documents/docker/calculatrice
```

This explicitly tells Docker Compose where the project directory is located.

The directory contains:

* `docker-compose.yml`
* `Dockerfile`
* `requirements.txt`
* the `app/` source directory

This option is required by the current script because `calc` can be executed from any directory.

Without an explicit project directory, Docker Compose would normally search for its Compose file using the current working directory and its parent directories. Since the user may run `calc` from somewhere unrelated to the project, Compose might not find the correct files.

### `up`

```bash
up
```

This creates and starts the services defined in `docker-compose.yml`.

If the required container does not exist, Compose creates it. If configuration or image changes require the container to be replaced, Compose recreates it.

### `-d`

```bash
-d
```

The `-d` option means **detached mode**.

The container runs in the background, and Docker Compose returns control to the script instead of remaining attached to the container’s output.

This allows the terminal to become available immediately after the calculator starts.

### `--build`

```bash
--build
```

This tells Docker Compose to perform the image build step before starting the service.

Docker does not necessarily rebuild every layer from the beginning. If the Dockerfile instructions and their associated files have not changed, Docker can reuse its cached layers.

When only `calculator.py` has changed, for example, Docker can normally reuse the system-library and Python-dependency layers and rebuild only the layers affected by the source-code modification.

---

**Line 8**

```bash
(
```

This opens a **subshell**.

The commands placed between `(` and `)` are executed in a separate Bash process.

This subshell acts as a background watcher. It waits for the calculator container to stop and then removes the temporary X11 authorization.

The complete subshell is sent to the background by the `&` operator on line 11. Meanwhile, the main script continues without waiting for the calculator to close.

---

**Line 9**

```bash
  container_id=$(docker compose --project-directory /home/philippe86220/Documents/docker/calculatrice ps -q calculator)
```

This retrieves the container ID associated with the `calculator` service and stores it in the `container_id` variable.

### `docker compose ps -q calculator`

```bash
docker compose ... ps -q calculator
```

* `ps` lists the containers managed by the Compose project.
* `calculator` restricts the result to the service named `calculator`.
* `-q`, meaning **quiet**, prints only the container ID instead of displaying the usual formatted table.

### Command substitution

```bash
$(...)
```

This is Bash command substitution.

Bash executes the command inside the parentheses and replaces the entire `$(...)` expression with the text written to standard output.

For example, if Compose returns:

```text
a4c8d92f731b
```

the assignment becomes equivalent to:

```bash
container_id="a4c8d92f731b"
```

The following lines assume that the `calculator` service was started successfully and that Compose returned a valid container ID.

---

**Line 10**

```bash
  docker wait "$container_id" > /dev/null
```

`docker wait` is a **blocking command**.

It waits until the specified container enters the stopped state.

This can happen when:

* the user closes the calculator window;
* the container is stopped manually with `docker stop`;
* the Python application terminates because of an error.

When the container stops, `docker wait` returns and normally prints the container’s exit code.

### Quoting the variable

```bash
"$container_id"
```

The double quotes prevent unwanted shell word splitting and pathname expansion.

A Docker container ID does not normally contain spaces, but quoting variable expansions is still good Bash practice.

### Discarding the output

```bash
> /dev/null
```

This redirects the standard output of `docker wait` to `/dev/null`.

`/dev/null` is a special system device that discards everything written to it.

Because the script does not need to display the container’s exit code, redirecting it avoids unnecessary terminal output.

---

**Line 11**

```bash
  xhost -local:docker > /dev/null 2>&1
```

After `docker wait` returns, the container has stopped.

The script then removes the X server authorization previously added with:

```bash
xhost +local:docker
```

### Standard output redirection

```bash
> /dev/null
```

This discards the informational message normally printed by `xhost`.

### Standard error redirection

```bash
2>&1
```

Bash uses numbered file descriptors:

* `1` represents standard output, or `stdout`.
* `2` represents standard error, or `stderr`.

The expression `2>&1` redirects standard error to the same destination currently used by standard output.

Because standard output has already been redirected to `/dev/null`, both output streams are discarded.

This allows the watcher to finish silently.

The authorization removed by this command belongs to the X server’s local connection family; it is not a permission associated exclusively with one particular container. This design is therefore best suited to the project’s intended single-user, single-instance use.

---

**Line 12**

```bash
) & disown
```

This line completes and detaches the background watcher.

### `)`

The closing parenthesis ends the subshell opened on line 7.

### `&`

The ampersand starts the entire subshell in the background.

The main script therefore does not wait for `docker wait` to finish. It immediately continues to the final confirmation message.

The background watcher and the calculator then run independently of the remaining commands in the main script.

### `disown`

`disown` removes the background job from the current Bash shell’s job table.

This prevents Bash from continuing to manage it as one of its active jobs and, in the usual terminal workflow, prevents the shell from sending its normal job-exit notification to that detached job when the terminal session ends.

It does not literally install a signal handler that makes the process universally immune to `SIGHUP`. Its practical purpose here is to allow the watcher to continue independently after the launching shell has finished.

Because the watcher does not need terminal input and its command output is redirected, it can continue waiting silently after the original terminal is closed.

---

**Line 14**

```bash
echo "Calculatrice lancée."
```

This displays a confirmation message to the user.

In English, the message could be written as:

```bash
echo "Calculator started."
```

The command is executed immediately after the background watcher has been launched.

It does not wait for the calculator window to close, so the terminal becomes available again almost immediately.

---

## Execution Flow Summary

1. The script grants the required local X11 authorization.
2. Docker Compose builds the image using its cache where possible.
3. Compose creates and starts the calculator container in detached mode.
4. A separate background subshell retrieves the container ID.
5. The subshell waits silently for that container to stop.
6. The main script displays a confirmation message and terminates, returning control of the terminal to the user.
7. The user operates the calculator normally.
8. When the calculator window is closed, the Python application exits.
9. The container stops because its main process has ended.
10. `docker wait` returns.
11. The background watcher removes the temporary X11 authorization.
12. The watcher terminates silently.

The complete sequence is:

```text
calc
  │
  ├─► Grant local X11 authorization
  │
  ├─► Build and start the container
  │
  ├─► Start the detached watcher
  │       │
  │       └─► docker wait <container_id>
  │
  └─► Display "Calculator started."
          Terminal becomes available again


Calculator window remains open
  │
  └─► Container continues running
          Watcher continues waiting


Calculator window is closed
  │
  └─► Python application exits
          │
          └─► Container stops
                  │
                  └─► docker wait returns
                          │
                          └─► Remove X11 authorization
                                  │
                                  └─► Watcher exits
```

---

## Important Scope and Limitations

This script is designed for:

* a Linux desktop system;
* Docker Compose;
* an available X11 or XWayland display;
* the project directory specified in the script;
* a single-user learning environment;
* one active calculator instance.

The project path is currently specific to the original system:

```text
/home/philippe86220/Documents/docker/calculatrice
```

Another user must replace this path with the actual location of the project on their own Linux system.

The script also assumes that:

* `DISPLAY` is defined in the environment;
* `xhost` is installed and can access the current display;
* the Docker service is available;
* the current user has permission to run Docker;
* the `calculator` service starts successfully;
* Docker Compose returns a valid container ID.

The automatic cleanup is triggered after `docker wait` detects that the container has stopped. It is therefore intended as a convenient mechanism for this controlled learning project, not as a complete general-purpose X11 authorization manager.

---

## Summary

The `calc` script acts as a small launcher and lifecycle manager for the graphical container.

It combines four operations:

1. Temporarily adjusts X11 access control.
2. Builds and starts the calculator container.
3. Creates a detached watcher that waits for the container to stop.
4. Removes the X11 authorization when the application closes.

From the user’s perspective, the workflow remains simple:

```bash
calc
```

starts the application, and closing the calculator window stops the container and triggers the X11 cleanup automatically.
