Installation
============

This add-on depends on `senaite.queue`_. If you don't have this add-on installed
yet, please follow the `Installation instructions of senaite.queue`_ first.

senaite.autopublish makes use of `Selenium WebDriver`_, a well-known tool
used for browser testing automation. Although this tool supports several browser
drivers, senaite.autopublish only supports `chromedriver`_. You have to
manually install the chrome browser and the chrome driver first. Please, refer
to `chromedriver versions selection documentation`_ for further details.

senaite.autopublish runs the browser in headless mode, but a graphical
interface in place in your system is required. Since your `SENAITE LIMS`_
instance is probably running in a server without graphical interface, we suggest
to install `xvfb`_ , a virtual framebuffer X server.

To install senaite.autopublish in your SENAITE instance, add this add-on in the
`eggs` section of your buildout configuration file as follows, and run
`bin/buildout` afterwards:

.. code-block:: ini

    [instance]
    ...
    eggs =
        ...
        senaite.autopublish


With this configuration, buildout will download and install the latest published
release of `senaite.autopublish from Pypi`_, as well as the `Selenium python
package`_, that provides python language bindings for `Selenium WebDriver`_.

Once buildout finishes, start the instance, login with a user with "Site
Administrator" privileges and activate the add-on:

http://localhost:8080/senaite/prefs_install_products_form


.. note:: It assumes you have a SENAITE zeo client listening to port 8080

.. Links

.. _senaite.autopublish from Pypi: https://pypi.org/project/senaite.autopublish
.. _senaite.queue: https://pypi.org/project/senaite.queue
.. _Installation instructions of senaite.queue: https://senaitequeue.readthedocs.io/en/latest/installation.html
.. _Selenium WebDriver: https://selenium.dev/
.. _Selenium python package: https://pypi.org/project/selenium/
.. _chromedriver: https://sites.google.com/a/chromium.org/chromedriver/getting-started
.. _chromedriver versions selection documentation: https://sites.google.com/a/chromium.org/chromedriver/downloads/version-selection
.. _xvfb: https://linux.die.net/man/1/xvfb
.. _SENAITE LIMS: https://www.senaite.com