.. image :: ./botbot/images/main-icon@300px.png
   :alt: B.O.T. Bot Program Robot Mascot Icon
   :align: center

B.O.T. Bot: Python Script Used for Baystone Media, Officite, and TherapySites Migraton
======================================================================================

This script is a website spider that uses the `Scrapy <https://github.com/scrapy/scrapy>`_ framework. It is specific to legacy websites from Baystone Media, Officite, and TherapySites.

The program uses the SMB Web Manager API as documented `here <https://dev-smbwebmgr.internetbrands.com/api-docs/index.html>`_. Production teams from Baystone Media, Officite, and TherapySites use the program as a tool to help migrate websites from legacy platforms to SMB Web Manager.

This program is frozen with `Pyinstaller <https://github.com/pyinstaller/pyinstaller>`_ for production teams to use without having to install Python and this project`s dependencies. Production teams use this tool as they are provisioning and setting up websites on SMB Web Manager.

How Is This Different than the Website Migration Tool (Website Importer, SMBWMGR-2666)?
=======================================================================================
* Specific to legacy websites.
* Remove 'bad' legacy website markup automatically.
* Crawl websites for internal links and create new pages from them.
  This program even uses NLP to make 'pretty'  page titles based on the ``href`` of the ``a`` tag of internal links. 
* In addition to markup, this program takes it a step further to migrate meta data, create redirects, add legacy stylesheets, etc.
* Cross-platform, **desktop** application that runs on all major operating systems.
* B.O.T. Bot is more a short-term, 'run-and-done' tool for the migration of all three brands to SMB Web Manager as fast as possible.

Target Websites
===============
* Officite SiteBuilder Legacy Websites.
* Baystone Media ColdFusion/Binary Minds Legacy Websites.
* TherapySites custinfo/CiNG Legacy Websites.
* Webmanager websites from any brand.

Features
========
* Works on legacy websites and webmanager websites from either of the three brands.
* Migrates markup, SEO meta data, images, documents, and legacy CSS.  
* Configures the SMB Web Manager navigation component.
* Configures the SMB Web Manager logo component.
* Creates 301 redirects for each crawled page.
* Creates new pages from internal links with 'pretty' page titles using NLP.
* User-friendly GUI with user feedback.

Installation
============

Python 3.5 or greater is required.

1. Clone this repository.
2. Install dependencies using `Pipenv <https://github.com/pypa/pipenv>`_ :

   pipenv install --dev

Usage
=====
1. Run ``botbot.py`` in its directory.
2. Follow the on-screen text user interface. The program requires only three inputs that you supply:

   * An access_token (gained from logging into the portal using an implicit grant type) used to call the SMB Web Manager API.
   * The URL of the home page of the legacy website to be migrated.
   * The site_id of the SMB Web Manager site to migrate information to.

3. In the event of an error while running this script, see the ``log_dev.txt`` file created when the program runs.

Alternatively, there in now a wxPython GUI for the program. Run ``botbotgui.py`` for usage.

TODO
=====
* Write better docstrings
* Write better unit tests
* Reduce program redundancy
* Scrape social media links
* Scrape legacy slider images
* Generalize this tool to be used on any website.
