0. Before you start
===================

It will be helpful to have these steps already completed before you
start the tutorial modules:

* Make sure you have `python 3.6`__ or newer.

__ https://www.python.org/downloads/release/python-360/

* Make sure you have `GNU make tools`__ and `compilers`__.

__ https://www.gnu.org/software/make/
__ https://gcc.gnu.org/


If docker is avilable for your system.

* Install `docker`__. If you cannot install docker, see the sigularity alternative below.

__ https://docs.docker.com/install/

* Download OpenFOAM image with:

.. code-block:: bash

    docker pull cfdengine/openfoam

* Download redis image with:

.. code-block:: bash

    docker pull redis

If docker is not available, you may want to try singularity.

* Download redis image if you are using singularity (this may require sudo):

.. code-block:: bash

    singularity pull redis.sif library://sylabs/examples/redis
