*Automatic publication of results for SENAITE LIMS*
===================================================

.. image:: https://img.shields.io/pypi/v/senaite.autopublish.svg?style=flat-square
    :target: https://pypi.python.org/pypi/senaite.autopublish

.. image:: https://img.shields.io/travis/senaite/senaite.autopublish/master.svg?style=flat-square
    :target: https://travis-ci.org/senaite/senaite.autopublish

.. image:: https://img.shields.io/github/issues-pr/senaite/senaite.autopublish.svg?style=flat-square
    :target: https://github.com/senaite/senaite.autopublish/pulls

.. image:: https://img.shields.io/github/issues/senaite/senaite.autopublish.svg?style=flat-square
    :target: https://github.com/senaite/senaite.autopublish/issues

.. image:: https://img.shields.io/badge/Made%20for%20SENAITE-%E2%AC%A1-lightgrey.svg
   :target: https://www.senaite.com


About
=====

This package enables the automatic and asynchronous publishing of results
reports, emailing included. User can choose multiple Samples in verified status
from samples listing and press the button "Auto publish" at the bottom of the
list. A confirmation is displayed and once the "Confirm" button is pressed, the
system delegates the publication process of the selected samples to
`senaite.queue`. This allows the sequential publication of large amounts of
samples in background, with just one click and with minimum impact on site
performance.

Installation
============

`senaite.autopublish` makes use of `Selenium WebDriver <https://selenium.dev/>`_,
a well-known tool used for browser testing automation: therefore, the
`selenium python package <https://pypi.org/project/selenium/>`_ , that provides
python language bindings for Selenium WebDriver, is automatically installed
after running bin/buildout with the egg `senaite.autopublish`.

Selenium WebDriver supports several browser drivers, but only
`chromedriver <https://sites.google.com/a/chromium.org/chromedriver/getting-started>`_
is supported by `senaite.autopublish`. After running bin/buildout, you still
need to install the chrome browser and the chrome browser driver. Refer to
`versions selection documentation <https://sites.google.com/a/chromium.org/chromedriver/downloads/version-selection>`_
for further details.

Although `senaite.autopublish` runs the browser in headless mode, you need to
have a graphical interface in place in your system. Since your SENAITE instance
is probably running in a server without graphical interface, we suggest to
install `xvfb <https://linux.die.net/man/1/xvfb>`_ , a virtual framebuffer X
server.

Remember that `senaite.autopublish` depends on `senaite.queue` and the latter
has to be properly configured too. Please, check the usage and configuration
instructions provided in `senaite.queue repository <https://github.com/senaite/senaite.queue`_.

Screenshots
===========

Confirmation view
-----------------

.. image:: https://raw.githubusercontent.com/senaite/senaite.autopublish/master/static/confirmation_view.png
   :alt: Confirmation view
   :width: 760px
   :align: center


Contribute
==========

We want contributing to SENAITE.AUTOPUBLISH to be fun, enjoyable, and educational
for anyone, and everyone. This project adheres to the `Contributor Covenant
<https://github.com/senaite/senaite.autopublish/blob/master/CODE_OF_CONDUCT.md>`_.

By participating, you are expected to uphold this code. Please report
unacceptable behavior.

Contributions go far beyond pull requests and commits. Although we love giving
you the opportunity to put your stamp on SENAITE.AUTOPUBLISH, we also are thrilled
to receive a variety of other contributions.

Please, read `Contributing to senaite.autopublish document
<https://github.com/senaite/senaite.autopublish/blob/master/CONTRIBUTING.md>`_.

If you wish to contribute with translations, check the project site on
`Transifex <https://www.transifex.com/senaite/senaite-autopublish/>`_.


Feedback and support
====================

* `Community site <https://community.senaite.org/>`_
* `Gitter channel <https://gitter.im/senaite/Lobby>`_
* `Users list <https://sourceforge.net/projects/senaite/lists/senaite-users>`_


License
=======

**SENAITE.AUTOPUBLISH** Copyright (C) 2019 Senaite Foundation

This program is free software; you can redistribute it and/or modify it under
the terms of the `GNU General Public License version 2
<https://github.com/senaite/senaite.autopublish/blob/master/LICENSE>`_ as published
by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
