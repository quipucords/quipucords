%{!?python3_sitelib: %define python3_sitelib %(%{__python3} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name: qpc
Version: 0.0.42
Release: 1%{?dist}
Summary: A tool for discovery and inspection of an IT environment.

Group: Applications/Internet
License: GPLv3
URL: http://github.com/quipucords/quipucords
Source0: http://github.com/quipucords/quipucords/archive/copr.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch: noarch

%if 0%{?rhel}%{?el6}%{?el7}
BuildRequires: epel-release
BuildRequires: python34-devel
BuildRequires: python34-setuptools
%endif
%if 0%{?fedora} >= 26
BuildRequires: python3-devel
BuildRequires: python3-setuptools
%endif
BuildRequires: pandoc
%if 0%{?rhel}%{?el6}%{?el7}
Requires: epel-release
Requires: python34
Requires: python34-requests
%endif
%if 0%{?fedora} >= 26
Requires: python3
Requires: python3-requests
%endif

%description
QPC is tool for discovery and inspection of an IT environment.

%prep
%setup -q

%build
%{__python3} setup.py build
make manpage

%install
rm -rf $RPM_BUILD_ROOT
%{__python3} setup.py install --skip-build --root $RPM_BUILD_ROOT
install -D -p -m 644 build/qpc.1 $RPM_BUILD_ROOT%{_mandir}/man1/qpc.1

%files
%defattr(-,root,root,-)
%doc README.rst AUTHORS.rst
%{_bindir}/qpc
%{python3_sitelib}/*
%{_mandir}/man1/qpc.1.gz

%changelog
* Fri Apr 13 2018 Kevan Holdaway <kholdawa@redhat.com> 0.0.42-1
- Allow true/false for boolean values in source options
- Enable editing the disable-ssl option for a source. <aaiken@redhat.com>
- Update man page to indicate ssl options cannot be used with network sources
* Wed Mar 14 2018 Ashley Aiken <aaiken@redhat.com> 0.0.41-1
- Fix scan list pagination support
* Thu Mar 8 2018 Ashley Aiken <aaiken@redhat.com> 0.0.40-1
- Flip disable-optional-products defaults. <aaiken@redhat.com>
- Remove satellite version from source options. <chambrid@redhat.com>
* Mon Mar 5 2018 Ashley Aiken <aaiken@redhat.com> 0.0.39-1
- Fix partial update for scan. <aaiken@redhat.com>
- Improve error handling for 500 response codes. <aaiken@redhat.com>
- Add report identifier as a lookup option for reports. <kholdawa@redhat.com>
* Fri Mar 2 2018 Ashley Aiken <aaiken@redhat.com> 0.0.38-1
- Remove scan status subcommand. <aaiken@redhat.com>
- Add scan support for exteneded product search. <aaiken@redhat.com>
- Enable ability to merge results of scan jobs. <kholdawa@redhat.com>
* Thu Mar 1 2018 Kevan Holdaway <kholdawa@redhat.com> 0.0.37-1
- Make scan options optional.
* Wed Feb 28 2018 Ashley Aiken <aaiken@redhat.com> 0.0.36-1
- Improve logging to capture command arguments. <aaiken@redhat.com>
- Improve logging to capture request method and endpoint. <aaiken@redhat.com>
- Fix report commands after scan job updates. <chambrid@redhat.com>
* Tue Feb 27 2018 Ashley Aiken <aaiken@redhat.com> 0.0.35-1
- Fix max-concurrency default for editing a scan.
* Fri Feb 23 2018 Ashley Aiken <aaiken@redhat.com> 0.0.34-1
- View all scan jobs for a scan by scan name.
- View scan job by identifier.
- Add feedback message to server config command.
* Thu Feb 22 2018 Ashley Aiken <aaiken@redhat.com> 0.0.33-1
- Add scan job support to command line for listing and clearing.
* Wed Feb 21 2018 Ashley Aiken <aaiken@redhat.com> 0.0.32-1
- Add scan edit support to command line and man documentation.
* Tue Feb 20 2018 Ashley Aiken <aaiken@redhat.com> 0.0.31-1
- Add scan creation, listing, showing, and start support to command line.
* Fri Feb 16 2018 Chris Hambridge <chambrid@redhat.com> 0.0.30-1
- Added logout subcommand to log out of server and remove token.
* Thu Feb 15 2018 Chris Hambridge <chambrid@redhat.com> 0.0.29-1
- Enable token expiration support in command line.
* Wed Feb 14 2018 Chris Hambridge <chambrid@redhat.com> 0.0.28-1
- Fix login issue required before command usage.
* Tue Feb 13 2018 Kevan Holdaway <kholdawa@redhat.com> 0.0.27-1
- Ensure ordering is preserved for source credentials from the command line.
- Require server configuration before other commands are executed.
* Wed Feb 7 2018 Chris Hambridge <chambrid@redhat.com> 0.0.26-1
- Added pagination support for credentials.
- Added pagination support for sources.
- Added pagination support for scans.
* Mon Feb 5 2018 Kevan Holdaway <kholdawa@redhat.com> 0.0.25-1
- Added detail report command with JSON or CSV output. <kholdawa@redhat.com>
- Add SSL options for vcenter sources. <chambrid@redhat.com>
- Add SSL options for satellite sources. <chambrid@redhat.com>
* Sun Feb 4 2018 Kevan Holdaway <kholdawa@redhat.com> 0.0.24-1
- Add report subcommand to provide summary report with JSON or CSV output.
* Fri Feb 2 2018 Chris Hambridge <chambrid@redhat.com> 0.0.23-1
- Check for client token before executing other subcommands.
* Wed Jan 31 2018 Chris Hambridge <chambrid@redhat.com> 0.0.22-1
- Enable HTTPS commnication support for the command line.
* Tue Jan 30 2018 Ashley Aiken <aaiken@redhat.com> 0.0.21-1
- Enhance scans with optional product support for JBoss EAP, Fuse, and BRMS.
* Thu Jan 25 2018 Chris Hambridge <chambrid@redhat.com> 0.0.20-1
- Removed dependency on pyxdg to support RHEL6 installation.
* Mon Jan 22 2018 Ashley Aiken <aaiken@redhat.com> 0.0.19-1
- Added become-method, become-user, and become-password support to credentials.
* Wed Jan 17 2018 Chris Hambridge <chambrid@redhat.com> 0.0.18-1
- Added support for satellite sources and options.
* Tue Jan 16 2018 Chris Hambridge <chambrid@redhat.com> 0.0.17-1
- Added support for satellite credentials.
* Mon Jan 15 2018 Chris Hambridge <chambrid@redhat.com> 0.0.16-1
- Enhanced command line with token authentication support.
* Thu Jan 11 2018 Ashley Aiken <aaiken@redhat.com> 0.0.15-1
- Incorporates partial update to allow for editing credentials.
* Sat Dec 16 2017 Chris Hambridge <chambrid@redhat.com> 0.0.14-1
- Add subcommand to display scan results
* Fri Dec 15 2017 Chris Hambridge <chambrid@redhat.com> 0.0.13-1
- Support scanning with multiple sources via scan start <chambrid@redhat.com>
- List scans by type and status <kholdawa@redhat.com>
* Thu Dec 7 2017 Kevan Holdaway <kholdawa@redhat.com> 0.0.12-1
- Enhance sources to support vcenter type along with existing network type.
- List sources by source type
- List credentials by credential type
* Wed Dec 6 2017 Kevan Holdaway <kholdawa@redhat.com> 0.0.11-1
- Enhance credentials to support vcenter type along with existing network type.
* Mon Dec 4 2017 Kevan Holdaway <kholdawa@redhat.com> 0.0.10-1
- Update subcommand from auth to cred
- Added error handling support for various Django Rest Framework outputs
* Fri Dec 1 2017 Kevan Holdaway <kholdawa@redhat.com> 0.0.9-1
- Update subcommand from profile to source
- Altered endpoint to sources and preparing multiple types.
* Thu Nov 30 2017 Kevan Holdaway <kholdawa@redhat.com> 0.0.8-1
- Update credentials endpoint to prepare multiple types.
* Wed Nov 29 2017 Kevan Holdaway <kholdawa@redhat.com> 0.0.7-1
- Enhancement to support Python 3.4, 3.5, and 3.6.
* Tue Nov 21 2017 Kevan Holdaway <kholdawa@redhat.com> 0.0.6-1
- Add server configuration command.
* Thu Nov 9 2017 Chris Hambridge <chambrid@redhat.com> 0.0.5-1
- Add capability to pause, cancel, and restart scans.
* Thu Nov 2 2017 Chris Hambridge <chambrid@redhat.com> 0.0.4-1
- Add handling for sshkeys with passphrase.
- Improve linting and code documentation.
* Wed Nov 1 2017 Chris Hambridge <chambrid@redhat.com> 0.0.3-1
- Add max_concurrency flag to the scan start command.
* Tue Oct 31 2017 Chris Hambridge <chambrid@redhat.com> 0.0.2-1
- Consolidate messages for content review.
* Fri Oct 17 2017 Chris Hambridge <chambrid@redhat.com> 0.0.1-1
- Initial release of quipucords command line.
- Allows credential management for hosts.
- Enables source management.
- Start, list and show scan operations.
