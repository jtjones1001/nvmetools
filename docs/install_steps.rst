Installation
============
.. code-block:: python

    pip install nvmetools

On Fedora Linux the nvmecmd utility must be granted access to read NVMe devices with the below
commands.  Running any console command, such as listnvme, displays the below commands with the actual
nvmecmd path.  Copy these commands into the terminal and run them.

.. code-block:: python

    sudo chmod 777 <path to nvmecmd>
    sudo setcap cap_sys_admin,cap_dac_override=ep <path to nvmecmd>

.. note::

    Most Test Suites use fio to generate IO traffic and therefore this must be installed before
    running any Test Suites.  fio can be found here: https://github.com/axboe/fio

.. warning::

    It is likely other Linux distributions require the same or similar steps but these have not been
    tested.