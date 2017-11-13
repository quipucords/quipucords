%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name: qpc
Version: 0.0.1
Release: 1%{?dist}
Summary: A tool for discovery and inspection of an IT environment.

Group: Applications/Internet
License: GPLv3
URL: http://github.com/quipucords/quipucords
Source0: http://github.com/quipucords/quipucords/archive/master.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch: noarch
BuildRequires: python3-devel
BuildRequires: python3-setuptools
BuildRequires: %{py3_dist Sphinx}
%{?rhel:Requires: epel-release}
Requires: %{py3_dist future}
Requires: %{py3_dist pyxdg}
Requires: %{py3_dist requests}

%description
QPC is tool for discovery and inspection of an IT environment.

%prep
%setup -q

%build
%{__python} setup.py build
make manpage

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --skip-build --root $RPM_BUILD_ROOT
install -D -p -m 644 docs/build/man/qpc.1 $RPM_BUILD_ROOT%{_mandir}/man1/qpc.1

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc README.rst AUTHORS.rst
%{_bindir}/qpc
%{python_sitelib}/*
%{_mandir}/man1/qpc.1.gz

%changelog
* Mon Nov 13 2017 Chris Hambridge <chambrid@redhat.com> 0.0.1-1
- Initial release of quipucords command line.
- Allows credential management for hosts.
- Enables network profile management.
- Controls basic host scan operations.
