#
# Copyright OpenEmbedded Contributors
#
# SPDX-License-Identifier: MIT
#

#
# This is for perl modules that use the new Build.PL build system
#
inherit cpan-base perlnative perldeps

EXTRA_CPAN_BUILD_FLAGS ?= ""

# Env var which tells perl if it should use host (no) or target (yes) settings
export PERLCONFIGTARGET = "${@is_target(d)}"
export PERL_ARCHLIB = "${STAGING_LIBDIR}${PERL_OWN_DIR}/perl5/${@get_perl_version(d)}/${@get_perl_arch(d)}"
export PERLHOSTLIB = "${STAGING_LIBDIR_NATIVE}/perl5/${@get_perl_version(d)}/"
export PERLHOSTARCHLIB = "${STAGING_LIBDIR_NATIVE}/perl5/${@get_perl_version(d)}/${@get_perl_hostarch(d)}/"
export LD = "${CCLD}"

cpan_build_do_configure () {
	if [ "${@is_target(d)}" = "yes" ]; then
		# build for target
		. ${STAGING_LIBDIR}/perl5/config.sh
	fi

	perl Build.PL --installdirs vendor --destdir ${D} \
			${EXTRA_CPAN_BUILD_FLAGS}

	# Build.PLs can exit with success without generating a
	# Build, e.g. in cases of missing configure time
	# dependencies. This is considered a best practice by
	# cpantesters.org. See:
	#  * http://wiki.cpantesters.org/wiki/CPANAuthorNotes
	#  * http://www.nntp.perl.org/group/perl.qa/2008/08/msg11236.html
	[ -e Build ] || bbfatal "No Build was generated by Build.PL"
}

cpan_build_do_compile () {
        perl Build --perl "${bindir}/perl" verbose=1
}

cpan_build_do_install () {
	perl Build install --destdir ${D}
}

EXPORT_FUNCTIONS do_configure do_compile do_install
