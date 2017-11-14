%{!?python3_sitelib: %define python3_sitelib %(%{__python3} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name: qpc
Version: 0.0.1
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
%endif
%if 0%{?fedora} >= 26
Requires: python3
%endif
Requires: pyxdg
Requires: python3-requests

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

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc README.rst AUTHORS.rst
%{_bindir}/qpc
%{python3_sitelib}/*
%{_mandir}/man1/qpc.1.gz

%changelog
* Mon Nov 13 2017 Chris Hambridge <chambrid@redhat.com> 0.0.1-1
- Initial release of quipucords command line.
- Allows credential management for hosts.
- Enables network profile management.
- Controls basic host scan operations.
