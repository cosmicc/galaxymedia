#!/usr/bin/python3

import os
import apt

SYNAPTIC_PINFILE = "/var/lib/synaptic/preferences"

def clean(cache,depcache):
    """ unmark (clean) all changes from the given depcache """
    # mvo: looping is too inefficient with the new auto-mark code
    # for pkg in cache.Packages:
    #    depcache.MarkKeep(pkg)
    depcache.init()


def saveDistUpgrade(cache,depcache):
    """ this functions mimics a upgrade but will never remove anything """
    depcache.upgrade(True)
    if depcache.del_count > 0:
        clean(cache,depcache)
    depcache.upgrade()

def get_update_packages():
    """
    Return a list of dict about package updates
    """
    pkgs = []

    apt.apt_pkg.init()
    # force apt to build its caches in memory for now to make sure
    # that there is no race when the pkgcache file gets re-generated
    apt.apt_pkg.config.set("Dir::Cache::pkgcache","")

    try:
        cache = apt.apt_pkg.Cache(apt.progress.base.OpProgress())
    except SystemError as e:
        sys.stderr.write("Error: Opening the cache (%s)" % e)
        sys.exit(-1)

    depcache = apt.apt_pkg.DepCache(cache)
    # read the pin files
    depcache.read_pinfile()
    # read the synaptic pins too
    if os.path.exists(SYNAPTIC_PINFILE):
        depcache.read_pinfile(SYNAPTIC_PINFILE)
    # init the depcache
    depcache.init()

    try:
        saveDistUpgrade(cache,depcache)
    except SystemError as e:
        sys.stderr.write("Error: Marking the upgrade (%s)" % e)
        sys.exit(-1)

    # use assignment here since apt.Cache() doesn't provide a __exit__ method
    # on Ubuntu 12.04 it looks like
    # aptcache = apt.Cache()
    for pkg in cache.packages:
        if not (depcache.marked_install(pkg) or depcache.marked_upgrade(pkg)):
            continue
        inst_ver = pkg.current_ver
        cand_ver = depcache.get_candidate_ver(pkg)
        if cand_ver == inst_ver:
            continue
        record = {"name": pkg.name,
                  "section": pkg.section,
                  "current_version": inst_ver.ver_str if inst_ver else '-',
                  "candidate_version": cand_ver.ver_str  if cand_ver else '-',
                  "priority": cand_ver.priority_str}
        pkgs.append(record)

    return pkgs


def ispending_updates():
    pkgs = get_update_packages()
    if len(pkgs) == 0:
    #  log.debug('NO pending updates detected on server')    
        return False
    else:
    #  log.debug('Pending updates ARE available on server')
        return True
