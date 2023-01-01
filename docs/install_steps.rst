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


.. warning::

    It is likely other Linux distributions require the same or similar steps but these have not been
    tested.