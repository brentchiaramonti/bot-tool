Pyinstaller build.spec Files
============================

Theses files are used when freezing the program using `Pyinstaller <https://github.com/pyinstaller/pyinstaller>`_.
These files are specific to the OS that the program will be run on. At the time of this writing (6/14/18), the
program has actually already been distributed to production teams from Baystone Media, Officite, and TherapySites.
Pyinstaller has options to create single-file executables for Windows, MacOS, and Linux. These provided files create
such single-file executables for Windows and MacOS.

Build Instructions
==================
1. Be sure to install Pyinstaller from within your Python development environment. Using ``pipenv``:

   pipenv install pyinstaller

2. ``cd`` to  the ``botbot`` directory.

3. Run Pyinstaller in the ``botbot`` directory and provide the ``build.spec`` file as a command line argument:

   pyinstaller build.spec

   Note: To prevent issues with paths, it may be necessary to copy build.spec files into the ``botbot`` directory.
   Then, run the above command.
