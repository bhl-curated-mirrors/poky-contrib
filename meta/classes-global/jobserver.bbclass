JOBSERVER_FIFO ?= ""
JOBSERVER_FIFO[doc] = "Path to external jobserver fifo to use instead of creating a per-build server."

JOBSERVER_IGNORE ?= ""
JOBSERVER_IGNORE[doc] = "Space separated list of packages that shouldn't be configured to use the jobserver feature."

addhandler jobserver_setup_fifo
jobserver_setup_fifo[eventmask] = "bb.event.ConfigParsed"

python jobserver_setup_fifo() {
    # don't setup a per-build fifo, if an external one is configured
    if d.getVar("JOBSERVER_FIFO"):
        return

    # don't use a job-server if no parallelism is configured
    jobs = oe.utils.parallel_make(d)
    if jobs in (None, 1):
        return

    # reduce jobs by one as a token has implicitly been handed to the
    # process requesting tokens
    jobs -= 1

    fifo = d.getVar("TMPDIR") + "/jobserver_fifo"

    # an old fifo might be lingering; remove it
    if os.path.exists(fifo):
        os.remove(fifo)

    # create a new fifo to use for communicating tokens
    os.mkfifo(fifo)

    # fill the fifo with the number of tokens to hand out
    wfd = os.open(fifo, os.O_RDWR)
    written = os.write(wfd, b"+" * jobs)
    if written != (jobs):
        bb.error("Failed to fil make fifo: {} != {}".format(written, jobs))

    # configure the per-build fifo path to use
    d.setVar("JOBSERVER_FIFO", fifo)
}

python () {
    # don't configure the fifo if none is defined
    fifo = d.getVar("JOBSERVER_FIFO")
    if not fifo:
        return

    # don't configure the fifo if the package wants to ignore it
    if d.getVar("PN") in (d.getVar("JOBSERVER_IGNORE") or "").split():
        return

    # avoid making make-native or its dependencies depend on make-native itself
    if d.getVar("PN") in (
                "make-native",
                "libtool-native",
                "pkgconfig-native",
                "automake-native",
                "autoconf-native",
                "m4-native",
                "texinfo-dummy-native",
                "gettext-minimal-native",
                "quilt-native",
                "gnu-config-native",
            ):
        return

    # don't make unwilling recipes depend on make-native
    if d.getVar('INHIBIT_DEFAULT_DEPS', False):
        return

    # make other recipes depend on make-native to make sure it is new enough to
    # support the --jobserver-auth=fifo:<path> syntax (from make-4.4 and onwards)
    d.appendVar("DEPENDS", " virtual/make-native")

    # disable the "-j <jobs>" flag, as that overrides the jobserver fifo tokens
    d.setVar("PARALLEL_MAKE", "")
    d.setVar("PARALLEL_MAKEINST", "")

    # set and export the jobserver in the environment
    d.appendVar("MAKEFLAGS", " --jobserver-auth=fifo:" + fifo)
    d.setVarFlag("MAKEFLAGS", "export", "1")

    # ignore the jobserver argument part of MAKEFLAGS in the hash, as that
    # shouldn't change the build output
    d.appendVarFlag("MAKEFLAGS", "vardepvalueexclude", "| --jobserver-auth=fifo:" + fifo)
}
