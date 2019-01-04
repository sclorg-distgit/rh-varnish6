%global scl_name_prefix  rh-
%global scl_name_base    varnish
%global scl_name_version 6
%global scl              %{scl_name_prefix}%{scl_name_base}%{scl_name_version}
%{!?nfsmountable: %global nfsmountable 1}
%scl_package %scl

# do not produce empty debuginfo package
%global debug_package %{nil}

Summary:       Package that installs %scl
Name:          %scl_name
Version:       4.1
Release:       3.bs1%{?dist}
License:       GPLv2+
Group: Applications/File
Source0: README
Source1: LICENSE
Source2: README.7

BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: scl-utils-build
# Temporary work-around
BuildRequires: iso-codes
BuildRequires: help2man

Requires: %{scl_prefix}varnish

%description
This is the main package for %scl Software Collection.

%package runtime
Summary:   Package that handles %scl Software Collection.
Requires:  scl-utils
Requires(post): policycoreutils-python

%description runtime
Package shipping essential scripts to work with %scl Software Collection.

%package build
Summary:   Package shipping basic build configuration
Requires:  scl-utils-build

%description build
Package shipping essential configuration macros to build %scl Software Collection.

%package scldevel
Summary:   Package shipping development files for %scl
Group:     Development/Languages

%description scldevel
Package shipping development files, especially usefull for development of
packages depending on %scl Software Collection.

%prep
%setup -c -T

# copy the license file so %%files section sees it
cp %{SOURCE0} .
cp %{SOURCE1} .
cp %{SOURCE2} .

expand_variables() {
    sed -i 's|%%{scl_name}|%{scl_name}|g' "$1"
    sed -i 's|%%{_scl_root}|%{_scl_root}|g' "$1"
    sed -i 's|%%{version}|%{version}|g' "$1"
%if 0%{?rhel} > 6
    sed -i 's|%%{start_command}|systemctl start %{scl_name}-varnish|g' "$1"
%else
    sed -i 's|%%{start_command}|service %{scl_name}-varnish start|g' "$1"
%endif
}

expand_variables README.7
expand_variables README

# Not required for now
#export LIBRARY_PATH=%{_libdir}\${LIBRARY_PATH:+:\${LIBRARY_PATH}}
#export LD_LIBRARY_PATH=%{_libdir}\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}

cat <<EOF | tee enable
export PATH=%{_bindir}:%{_sbindir}\${PATH:+:\${PATH}}
export LIBRARY_PATH=%{_libdir}\${LIBRARY_PATH:+:\${LIBRARY_PATH}}
export LD_LIBRARY_PATH=%{_libdir}\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}
export MANPATH=%{_mandir}:\${MANPATH}
export CPATH=%{_includedir}\${CPATH:+:\${CPATH}}
EOF

# generate rpm macros file for depended collections
cat << EOF | tee scldev
%%scl_%{scl_name_base}         %{scl}
%%scl_prefix_%{scl_name_base}  %{scl_prefix}
EOF

%build
# generate a helper script that will be used by help2man
cat >h2m_helper <<'EOF'
#!/bin/bash
[ "$1" == "--version" ] && echo "%{scl_name} %{version} Software Collection" || cat README
EOF
chmod a+x h2m_helper

# generate the man page
help2man -N --section 7 ./h2m_helper -o %{scl_name}.7


%install
mkdir -p %{buildroot}%{_scl_scripts}/root
install -m 644 enable  %{buildroot}%{_scl_scripts}/enable
install -D -m 644 scldev %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel

# install generated man page
mkdir -p %{buildroot}%{_mandir}/man1/
mkdir -p %{buildroot}%{_mandir}/man7/
mkdir -p %{buildroot}%{_mandir}/man8/
mkdir -p %{buildroot}%{_libdir}/pkgconfig/
mkdir -p %{buildroot}%{_datadir}/aclocal/
mkdir -p %{buildroot}%{_datadir}/licenses/
install -m 644 README.7 %{buildroot}%{_mandir}/man7/%{scl_name}.7

%scl_install

# create directory for SCL register scripts
mkdir -p %{buildroot}%{?_scl_scripts}/register.content
mkdir -p %{buildroot}%{?_scl_scripts}/register.d
cat <<EOF | tee %{buildroot}%{?_scl_scripts}/register
#!/bin/sh
ls %{?_scl_scripts}/register.d/* | while read file ; do
    [ -x \$f ] && source \$(readlink -f \$file)
done
EOF
# and deregister as well
mkdir -p %{buildroot}%{?_scl_scripts}/deregister.d
cat <<EOF | tee %{buildroot}%{?_scl_scripts}/deregister
#!/bin/sh
ls %{?_scl_scripts}/deregister.d/* | while read file ; do
    [ -x \$f ] && source \$(readlink -f \$file)
done
EOF

%post runtime
# Simple copy of context from system root to DSC root.
# In case new version needs some additional rules or context definition,
# it needs to be solved.
# Unfortunately, semanage does not have -e option in RHEL-5, so we have to
# have its own policy for collection
semanage fcontext -a -e / %{_scl_root} >/dev/null 2>&1 || :
restorecon -R %{_scl_root} >/dev/null 2>&1 || :
selinuxenabled && load_policy || :

%files

%files runtime
%defattr(-,root,root)
%doc README LICENSE
%scl_files
%dir %{_mandir}/man1
%dir %{_mandir}/man3
%dir %{_mandir}/man7
%dir %{_mandir}/man8
%dir %{_libdir}/pkgconfig
%dir %{_datadir}/aclocal
%dir %{_datadir}/licenses
%{_mandir}/man7/%{scl_name}.*
%attr(0755,root,root) %{?_scl_scripts}/register
%attr(0755,root,root) %{?_scl_scripts}/deregister
%{?_scl_scripts}/register.content
%dir %{?_scl_scripts}/register.d
%dir %{?_scl_scripts}/deregister.d

%files build
%defattr(-,root,root)
%{_root_sysconfdir}/rpm/macros.%{scl}-config

%files scldevel
%defattr(-,root,root)
%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel

%changelog
* Tue Oct 23 2018 Luboš Uhliarik <luhliari@redhat.com> - 4.1-3
- varnish6 doesn't own /opt/rh/rh-varnish6/root/usr/share/licenses (#1608952)

* Wed Jul 18 2018 Luboš Uhliarik <luhliari@redhat.com> - 4.1-2
- update for Varnish 6 (#1588045)

* Wed Dec 13 2017 Joe Orton <jorton@redhat.com> - 3.1-1
- update for Varnish 5 (#1518821)

* Tue Oct 13 2015 Jan Kaluza <jkaluza@redhat.com> - 2.1-6
- correct mistakes in man page (#1261372)

* Fri Sep 11 2015 Jan Kaluza <jkaluza@redhat.com> - 2.1-5
- own man3 directory (#1261455)
- improve the man page (#1261372)

* Mon Aug 17 2015 Jan Kaluza <jkaluza@redhat.com> - 2.1-4
- add sbin directory into PATH (#1253666)

* Wed Jul 08 2015 Jan Kaluza <jkaluza@redhat.com> - 2.1-3
- rebuild against new scl-utils

* Tue Jul 07 2015 Jan Kaluza <jkaluza@redhat.com> - 2.1-2
- enable NFS support

* Wed Apr 08 2015 Jan Kaluza <jkaluza@redhat.com> - 2.1-1
- initial packaging