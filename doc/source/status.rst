Current status of python-subgrid, subgrid and 3di
=================================================

To get some overview and to have a central place where to find
information, here's a short list.


Fortran subgrid library
-----------------------

Code location: in deltares' svn.
https://repos.deltares.nl/repos/3Di/trunk/subgridf90

Tags are made semi-automatically with a script from
https://github.com/nens/threedi-infrastructure, via a
manually-maintained list of revision numbers in
https://github.com/nens/threedi-infrastructure/blob/master/threedi_infrastructure/fortran.py

It is tested with jenkins: http://jenkins.3di.lizard.net/

Again with a semi-automatic method, ubuntu packages for the 12.04 LTS
release are made with https://github.com/nens/threedi-infrastructure,
see http://jenkins.3di.lizard.net/ubuntu/precise64/ . This includes
the "fortrangis" library, of which a custom copy is included in the
subgrid svn repo.

Installation instructions for the ubuntu packages are linked from the
jenkins homepage.

.. note::

    For access to the deltares svn repos, you'll need to mail `Arthur
    van Dam <mailto:Arthur.vanDam@deltares.nl>`_. For access to the
    protected github repositories (you'll get a 404 if you don't have
    access), mail `Reinout van Rees
    <mailto:reinout.vanrees@nelen-schuurmans.nl>`_. Also mail Reinout
    for extra access to the jenkins site.


Python-subgrid wrapper (this project)
-------------------------------------

Code location: https://github.com/nens/python-subgrid (it used to be
in deltares' svn, but tags are harder there and github pull requests
are very important to have).

Tags are automatically generated into proper Python packages:
http://jenkins.3di.lizard.net/packages/ .
https://github.com/nens/threedi-infrastructure sets up this automatic
package building.

It is tested with jenkins: http://jenkins.3di.lizard.net/

Every time a new commit is made, a fresh version of the documentation
(including this file) is generated into
http://jenkins.3di.lizard.net/doc/ by the jenkins testrunner.


3di live site(s)
----------------

Code location: https://github.com/nens/threedi-server/ .

This is the basis for the http://live.3di.lizard.net/ websites.
