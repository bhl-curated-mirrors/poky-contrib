SRCBRANCH ?= "master"
PV = "2.40+git"
SRCREV_glibc ?= "4228baef1a94e8bde84ad74f2e0358120a2bcac7"
SRCREV_localedef ?= "fab74f31b3811df543e24b6de47efdf45b538abc"

GLIBC_GIT_URI ?= "git://sourceware.org/git/glibc.git;protocol=https"

UPSTREAM_CHECK_GITTAGREGEX = "(?P<pver>\d+\.\d+(\.(?!90)\d+)*)"

CVE_STATUS[CVE-2023-4911] = "fixed-version: Fixed in stable branch updates"
