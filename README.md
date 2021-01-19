A simple web-based ARM assembler simulator for educational purposes.

User enters assembler code, it is compiled and run in in a sandbox.
Then, register values at the end of the program are printed.

That's pretty much it.

Originally developed for [KSP][KSP], the Czech computer science seminar
for high school students. If you speak Czech, you can learn about ARM
assembly in our tutorail series: [part 1][], [part 2][], [part 3][], [part 4][].

[KSP]: https://ksp.mff.cuni.cz/
[part 1]: https://ksp.mff.cuni.cz/h/ulohy/30/zadani1.html#task-30-1-7
[part 2]: https://ksp.mff.cuni.cz/h/ulohy/30/zadani2.html#task-30-2-7
[part 3]: https://ksp.mff.cuni.cz/h/ulohy/30/zadani3.html#task-30-3-7
[part 4]: https://ksp.mff.cuni.cz/h/ulohy/30/zadani4.html#task-30-4-7


# Installation & dependencies

Tested on Debian Buster. For other distros, adapt as needed.

1. Install dependencies:

        apt install gcc-arm-linux-gnueabihf qemu-user python3-flask libcap-dev uwsgi uwsgi-plugin-python3 build-essential

2. Download and install `isolate` from https://github.com/ioi/isolate/

3. Run asm.py as you would any Flask app. Recommended deployment is uwsgi + nginx
   (use provided `asm.ini`). For simple testing, you can also use uwsgi's built-in
   HTTP server `uwsgi --ini asm-http.ini`, starts HTTP server on 0.0.0.0:6173 and
   either use it directly or put it behind a reverse proxy.

