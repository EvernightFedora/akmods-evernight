## START: Set by rpmautospec
## (rpmautospec version 0.8.3)
## RPMAUTOSPEC: autorelease, autochangelog
%define autorelease(e:s:pb:n) %{?-p:0.}%{lua:
    release_number = 3;
    base_release_number = tonumber(rpm.expand("%{?-b*}%{!?-b:1}"));
    print(release_number + base_release_number - 1);
}%{?-e:.%{-e*}}%{?-s:.%{-s*}}%{!?-n:%{?dist}}
## END: Set by rpmautospec

Name:           akmods-evernight
Version:        43.1
Release:        %autorelease
Summary:        Automatic kmods build and install tool

License:        MIT
URL:            http://rpmfusion.org/Packaging/KernelModules/Akmods

# We are upstream, these files are maintained directly in pkg-git
Source0:        95-akmods.preset
Source1:        akmods
Source2:        akmodsbuild
Source3:        akmods.h2m
Source6:        akmods.service
Source7:        akmods-shutdown
Source8:        akmods-shutdown.service
Source9:        README
Source10:       LICENSE
Source11:       akmods@.service
Source12:       akmods-ostree-post
Source13:       95-akmodsposttrans.install
Source14:       akmods.log
Source15:       README.secureboot
Source16:       cacert.config.in
Source17:       akmods-kmodgenca
Source18:       akmods-keygen.target
Source19:       akmods-keygen@.service
Source20:       %{name}-tmpfiles.conf
Source21:       akmods.sysusers.conf

BuildArch:      noarch

BuildRequires:  help2man

# Needed for older branches el8+, noop on f43+
%{?sysusers_requires_compat}

# not picked up automatically
Requires:       %{_bindir}/flock
Requires:       %{_bindir}/time

# Conflict with original akmods
Conflicts:     akmods

# needed for actually building kmods:
Requires:       %{_bindir}/rpmdev-vercmp
Requires:       kmodtool >= 1.1-1

# needed to create CA/Keypair to sign modules
Requires:       openssl

# this should track in all stuff that is normally needed to compile modules:
Requires:       bzip2 coreutils diffutils file findutils gawk gcc grep
Requires:       gzip make sed tar unzip util-linux rpm-build

# On EL, kABI list was renamed
%if 0%{?rhel}
Requires:       (kernel-abi-stablelists if kernel-core)
%endif

# We use a virtual provide that would match either
# kernel-devel or kernel-PAE-devel
Requires:       kernel-devel-uname-r
# kernel-devel-matched enforces the same kernel version as the -devel
%if 0%{?fedora} || 0%{?rhel} >= 9
Requires:       (kernel-debug-devel-matched if kernel-debug-core)
Requires:       (kernel-devel-matched if kernel-core)
%else
Suggests:       (kernel-debug-devel if kernel-debug-core)
Suggests:       (kernel-devel if kernel-core)
%endif
Suggests:       (kernel-rt-devel if kernel-rt)

# we create a special user that used by akmods to build kmod packages

# systemd unit requirements.
BuildRequires:  systemd
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
# Optional but good to have on recent kernel
Requires: pkgconfig(libelf)

# We need grubby or systemd-boot to know the default kernel
# On EL7 assumes grubby is there by default - rhbz#2124086
%if 0%{?fedora} || 0%{?rhel} > 7
Requires: (grubby or sdubby)
%endif

%description
Akmods startup script will rebuild akmod packages during system
boot, while its background daemon will build them for kernels right
after they were installed.


%prep
%setup -q -c -T
cp -p %{SOURCE9} %{SOURCE10} %{SOURCE15} .


%build
# Nothing to build


%install
mkdir -p %{buildroot}%{_usrsrc}/%{name} \
         %{buildroot}%{_sbindir} \
         %{buildroot}%{_sysconfdir}/rpm \
         %{buildroot}%{_sysconfdir}/pki/%{name}/certs \
         %{buildroot}%{_sysconfdir}/pki/%{name}/private \
         %{buildroot}%{_sysconfdir}/kernel/postinst.d \
         %{buildroot}%{_sysconfdir}/logrotate.d \
         %{buildroot}%{_localstatedir}/cache/%{name} \
         %{buildroot}%{_localstatedir}/log/%{name} \
         %{buildroot}%{_tmpfilesdir}

install -pm 0755 %{SOURCE1} %{buildroot}%{_sbindir}/
install -pm 0755 %{SOURCE2} %{buildroot}%{_sbindir}/
install -pm 0755 %{SOURCE12} %{buildroot}%{_sbindir}/
install -pm 0644 %{SOURCE14} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
install -pm 0640 %{SOURCE16} %{buildroot}%{_sysconfdir}/pki/%{name}/
install -pm 0755 %{SOURCE17} %{buildroot}%{_sbindir}/kmodgenca
install -pm 0644 %{SOURCE20} %{buildroot}%{_tmpfilesdir}/%{name}.conf
install -dpm 0770 %{buildroot}%{_rundir}/%{name}/

mkdir -p %{buildroot}%{_prefix}/lib/kernel/install.d
install -pm 0755 %{SOURCE13} %{buildroot}%{_prefix}/lib/kernel/install.d/
mkdir -p \
         %{buildroot}%{_unitdir} \
         %{buildroot}%{_presetdir}

install -pm 0644 %{SOURCE0} %{buildroot}%{_presetdir}/
install -pm 0644 %{SOURCE6} %{buildroot}%{_unitdir}/
install -pm 0755 %{SOURCE7} %{buildroot}%{_sbindir}/
install -pm 0644 %{SOURCE8} %{buildroot}%{_unitdir}/
install -pm 0644 %{SOURCE11} %{buildroot}%{_unitdir}/
install -pm 0644 %{SOURCE18} %{buildroot}%{_unitdir}/
install -pm 0644 %{SOURCE19} %{buildroot}%{_unitdir}/

# Generate and install man pages.
mkdir -p %{buildroot}%{_mandir}/man1
help2man -N -i %{SOURCE3} -s 1 \
    -o %{buildroot}%{_mandir}/man1/akmods.1 \
       %{buildroot}%{_sbindir}/akmods
help2man -N -i %{SOURCE3} -s 1 \
    -o %{buildroot}%{_mandir}/man1/akmodsbuild.1 \
       %{buildroot}%{_sbindir}/akmodsbuild

install -m0644 -D %{SOURCE21} %{buildroot}%{_sysusersdir}/akmods.conf


%pre
%sysusers_create_compat %{SOURCE21}

%post
%systemd_post akmods.service
%systemd_post akmods@.service
%systemd_post akmods-shutdown.service

%preun
%systemd_preun akmods.service
%systemd_preun akmods@.service
%systemd_preun akmods-shutdown.service

%postun
%systemd_postun akmods.service
%systemd_postun akmods@.service
%systemd_postun akmods-shutdown.service


%files
%doc README README.secureboot
%license LICENSE
%{_sbindir}/akmodsbuild
%{_sbindir}/akmods
%{_sbindir}/akmods-ostree-post
%{_sbindir}/kmodgenca
%dir %attr(750,root,akmods) %{_sysconfdir}/pki/%{name}/certs
%dir %attr(750,root,akmods) %{_sysconfdir}/pki/%{name}/private
%config(noreplace) %attr(640,root,akmods) %{_sysconfdir}/pki/%{name}/cacert.config.in
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%{_unitdir}/akmods.service
%{_unitdir}/akmods@.service
%{_sbindir}/akmods-shutdown
%{_unitdir}/akmods-shutdown.service
%{_prefix}/lib/kernel/install.d/95-akmodsposttrans.install
%attr(0644,root,root) %{_unitdir}/akmods-keygen.target
%attr(0644,root,root) %{_unitdir}/akmods-keygen@.service
%dir %attr(0770,root,akmods) %{_rundir}/%{name}
%{_tmpfilesdir}/%{name}.conf
# akmods was enabled in the default preset by f28
%if 0%{?rhel}
%{_presetdir}/95-akmods.preset
%else
%exclude %{_presetdir}/95-akmods.preset
%endif
%{_usrsrc}/akmods
%dir %attr(-,akmods,akmods) %{_localstatedir}/cache/akmods
%dir %attr(0775,root,akmods) %{_localstatedir}/log/%{name}
%{_mandir}/man1/*
%{_sysusersdir}/akmods.conf


%changelog
## START: Generated by rpmautospec
* Thu Nov 06 2025 Luan Vitor Simião oliveira <luanv.oliveira@outlook.com> - 0.6.2-3
- fix: prevent akmods@ on offline update on fc43+

* Wed Oct 15 2025 Nicolas Chauvet <kwizart@gmail.com> - 0.6.2-2
- Add compat for sysusers support

* Wed Oct 01 2025 Nicolas Chauvet <kwizart@gmail.com> - 0.6.2-1
- Update to 0.6.2

* Wed Oct 01 2025 Nicolas Chauvet <kwizart@gmail.com> - 0.6.1-6
- akmods: add missing sysusers group

* Wed Oct 01 2025 Nicolas Chauvet <kwizart@gmail.com> - 0.6.1-5
- docs: drop grep Issuer from mokutil output

* Mon Sep 22 2025 Nicolas Chauvet <kwizart@gmail.com> - 0.6.1-4
- Drop akmodsinit

* Mon Sep 22 2025 Nicolas Chauvet <kwizart@gmail.com> - 0.6.1-3
- Rework akmod.service installation

* Mon Sep 22 2025 Nicolas Chauvet <kwizart@gmail.com> - 0.6.1-2
- Add akmods-sysusers.conf

* Mon Sep 22 2025 Nicolas Chauvet <kwizart@gmail.com> - 0.6.1-1
- Update to 0.6.1

* Mon Sep 22 2025 Nicolas Chauvet <kwizart@gmail.com> - 0.6.0-25
- Drop nohup requires for rhel6

* Mon Sep 22 2025 Nicolas Chauvet <kwizart@gmail.com> - 0.6.0-24
- Rework sysusers

* Mon Sep 22 2025 Nicolas Chauvet <kwizart@gmail.com> - 0.6.0-23
- Case for unspecified target - rhbz#2394562

* Mon Sep 22 2025 Nicolas Chauvet <kwizart@gmail.com> - 0.6.0-22
- Drop global armv7hl target override and default

* Wed Sep 17 2025 Nicolas Chauvet <kwizart@gmail.com> - 0.6.0-21
- akmods: drop grubby symlink test

* Wed Sep 17 2025 Francis Montagnac <francis.montagnac@free.fr> - 0.6.0-20
- akmods: wrong calls to check_kernel_devel - rhbz#2376351

* Wed Sep 17 2025 Francis Montagnac <francis.montagnac@free.fr> - 0.6.0-19
- akmods: check_default_kernel is never called - rhbz#2376351

* Wed Sep 17 2025 Nicolas Chauvet <kwizart@gmail.com> - 0.6.0-18
- Drop nohup usage

* Wed Sep 17 2025 Fedora Release Engineering <releng@fedoraproject.org> - 0.6.0-17
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Wed Sep 17 2025 Leigh Scott <leigh123linux@gmail.com> - 0.6.0-16
- Fix changelog

* Wed Sep 03 2025 Daniel Hast <hast.daniel@protonmail.com> - 0.6.0-15
- fix: apply shellcheck recommendations

* Wed Jul 23 2025 Fedora Release Engineering <releng@fedoraproject.org> - 0.6.0-14
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Sat May 03 2025 Leigh Scott <leigh123linux@gmail.com> - 0.6.0-13
- Fix changelog

* Fri May 02 2025 Marcel Hetzendorfer <mh7596@gmail.com> - 0.6.0-11
- Show building and installing on plymouth boot screen

* Tue Feb 11 2025 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 0.6.0-10
- Add sysusers.d config file to allow rpm to create users/groups
  automatically

* Thu Jan 16 2025 Fedora Release Engineering <releng@fedoraproject.org> - 0.6.0-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Wed Dec 11 2024 Nicolas Chauvet <kwizart@gmail.com> - 0.6.0-8
- Update others hostname occurences

* Tue Dec 10 2024 Nicolas Chauvet <kwizart@gmail.com> - 0.6.0-7
- Drop hostname deps - rhbz#2330137

* Thu Nov 28 2024 Nicolas Chauvet <kwizart@gmail.com> - 0.6.0-6
- Validate or discard default_kernel - rhbz#2270414

* Fri Nov 08 2024 Nicolas Chauvet <kwizart@gmail.com> - 0.6.0-5
- Fix KEYNAME lengh - rhbz#2323702

* Wed Oct 02 2024 Rohan Barar <rohan.barar@gmail.com> - 0.6.0-4
- Add robust missing key pair logic

* Wed Oct 02 2024 Rohan Barar <rohan.barar@gmail.com> - 0.6.0-3
- Improved error handling + Bug fixes

* Tue Oct 01 2024 Rohan Barar <rohan.barar@gmail.com> - 0.6.0-2
- Add check for elevated privileges

* Tue Oct 01 2024 Nicolas Chauvet <kwizart@gmail.com> - 0.6.0-1
- Bump akmods version

* Tue Oct 01 2024 Nicolas Chauvet <kwizart@gmail.com> - 0.5.10-30
- Remove duplicate akmodsposttrans call - rhbz#2011120

* Thu Sep 26 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-29
- Avoid double error on empty user-provided key pair name.

* Thu Sep 26 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-28
- Corrected erroneous code introduced in previous commits.

* Thu Sep 26 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-27
- Fixed typo 'if' to 'fi'.

* Thu Sep 26 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-26
- Added check for existing key pair with same name as user-specified new
  key pair name.

* Thu Sep 26 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-25
- Added ability for user to name key pair.

* Sun Sep 22 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-24
- Introduced loop to gracefully handle extremely rare key pair name
  collision events.

* Sat Sep 21 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-23
- Refactor key pair naming scheme to enhance robustness + Removed collision
  check and key pair backup function due to bug with ':' in file names
  alongside superfluous nature of function given improved naming scheme.

* Sat Sep 21 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-22
- Removed 'sudo' prefixes as per request in PR #23.

* Sat Sep 21 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-21
- Further improvements to argument parsing logic.

* Fri Sep 20 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-20
- Improved clarity of exit status code comments.

* Fri Sep 20 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-19
- Revert "Utilise robust shebang." as per request on PR #23.

* Fri Sep 20 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-18
- Added support for combined single-letter arguments + Chowned symlinks.

* Fri Sep 20 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-17
- Improved mokutil error handling + Added sudo prefixes.

* Fri Sep 20 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-16
- Added error handling for failed cacert modification.

* Fri Sep 20 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-15
- Whitespace changes for consistency.

* Fri Sep 20 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-14
- Extract functions to enhance readability + Set 'commonName' to match
  'KEYNAME'.

* Fri Sep 20 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-13
- Added logic to detect broken existing key pairs.

* Fri Sep 20 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-12
- Improved user feedback in event of existing key pair.

* Fri Sep 20 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-11
- Updated copyright information.

* Fri Sep 20 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-10
- Various changes to avoid ShellCheck warnings.

* Fri Sep 20 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-9
- Align license to 80 character width.

* Fri Sep 20 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-8
- Utilise robust shebang.

* Fri Sep 20 2024 Rohan Barar <rohan.barar@gmail.com> - 0.5.10-7
- Removed hard-coded paths.

* Fri Aug 23 2024 Nicolas Chauvet <kwizart@gmail.com> - 0.5.10-6
- Fix parsing multiple kernel

* Fri Aug 23 2024 Nicolas Chauvet <kwizart@gmail.com> - 0.5.10-5
- Use check_kernel_devel return code as appropriate

* Fri Aug 23 2024 Nicolas Chauvet <kwizart@gmail.com> - 0.5.10-4
- Change check_kernel_devel() to return instead of exit

* Fri Aug 23 2024 Nicolas Chauvet <kwizart@gmail.com> - 0.5.10-3
- akmods --from-init only operates on current kernel

* Fri Aug 23 2024 Nicolas Chauvet <kwizart@gmail.com> - 0.5.10-2
- Deprecate akmods-shutdown script

* Fri Aug 23 2024 Nicolas Chauvet <kwizart@gmail.com> - 0.5.10-1
- Bump to akmods 0.5.10

* Fri Aug 23 2024 Nicolas Chauvet <kwizart@gmail.com> - 0.5.9-8
- Only check for default_kernel is no value - rhbz#2293047

* Fri Aug 23 2024 Nicolas Chauvet <kwizart@gmail.com> - 0.5.9-7
- Revert "Call Init before the argument parser"

* Fri Aug 23 2024 Nicolas Chauvet <kwizart@gmail.com> - 0.5.9-6
- Switch to use sdubby alternatives to grubby

* Fri Aug 23 2024 Nicolas Chauvet <kwizart@gmail.com> - 0.5.9-5
- Drop older rhel and use -core

* Fri Aug 23 2024 Nicolas Chauvet <kwizart@gmail.com> - 0.5.9-4
- Drop older rhel cases

* Mon Aug 19 2024 Jonathan Wakely <jwakely@fedoraproject.org> - 0.5.9-3
- Fix bug URLs in man page

* Wed Jul 17 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0.5.9-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Thu Jul 04 2024 Nicolas Chauvet <kwizart@gmail.com> - 0.5.9-1
- akmods release 0.5.9

* Thu Jul 04 2024 Hans de Goede <hdegoede@redhat.com> - 0.5.8-10
- Fix intel-ipu6-kmod installation with kernel >= 6.10

* Thu Jul 04 2024 Marius Schwarz <fedoradev@cloud-foo.de> - 0.5.8-9
- Call Init before the argument parser

* Mon Jan 22 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0.5.8-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Fri Jan 19 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0.5.8-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Tue Dec 05 2023 Nicolas Chauvet <kwizart@gmail.com> - 0.5.8-6
- Workaround for rhbz#1889136 when localpkg_gpgcheck=True

* Wed Jul 19 2023 Fedora Release Engineering <releng@fedoraproject.org> - 0.5.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Fri May 05 2023 Nicolas Chauvet <kwizart@gmail.com> - 0.5.8-1
- Don't emit weak-deps from deprecated arches on all
- Allow akmods --rebuild to force rebuild+reinstall - rhbz#2140012
- ensure to build for grub or systemd-boot default kernel - rhbz#2124086
- Drop "which" as akmods dependency



## END: Generated by rpmautospec
