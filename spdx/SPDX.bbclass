SPDX_VERSION = "SPDX-1.1"
DATA_LICENSE = "CC0-1.0"

python do_SPDX () {
    import os

    info = {} 
    info['workdir'] = (d.getVar('WORKDIR', True) or "")
    info['sourcedir'] = (d.getVar('S', True) or "")
    info['pn'] = (d.getVar( 'PN', True ) or "")
    info['pv'] = (d.getVar( 'PV', True ) or "")
    info['src_uri'] = (d.getVar( 'SRC_URI', True ) or "")
    info['spdx_version'] = (d.getVar('SPDX_VERSION', True) or '')
    info['data_license'] = (d.getVar('DATA_LICENSE', True) or '')

    outfile = "/home/yocto/fossology_scans/" + info['pn'] + ".spdx.out"
    info['spdxdir'] = info['workdir'] + "/spdx_temp"

    ## remove old log file, create tmp dir
    remove_file( outfile )
    if not os.path.exists( info['spdxdir'] ):
        os.makedirs( info['spdxdir'] )

    local_file_info, tar_file = setup_foss_scan( info )
    foss_file_info = parse_foss_scan( tar_file )
    info['tar_file'] = tar_file
    spdx_doc = create_spdx_doc( local_file_info, foss_file_info )
    spdx_header_info = get_header_info(info, local_file_info, foss_file_info)

    file = open( outfile, 'w+' )

    file.write( spdx_header_info + '\n' )
    for block in spdx_doc:
        file.write( block )

    file.close()

    ## clean up the temp stuff
    remove_dir_tree( info['spdxdir'] )
    remove_file( tar_file )
}
addtask SPDX after do_patch before do_configure

def setup_foss_scan( info ):
    import errno, shutil
    import tarfile
    file_info = {}
    for f_dir, f in list_files( info['sourcedir'] ):
        full_path =  os.path.join( f_dir, f )
        abs_path = os.path.join(info['sourcedir'], full_path)
        dest_dir = os.path.join( info['spdxdir'], f_dir )
        dest_path = os.path.join( info['spdxdir'], full_path )
        try:
            stats = os.stat(abs_path)
        except OSError as e:
            bb.warn( "Stat failed" + str(e) + "\n")
            continue

        checksum = hash_file( abs_path )
        mtime = time.asctime(time.localtime(stats.st_mtime))
        file_info[checksum] = {}
        file_info[checksum]['FileName'] = full_path

        try:
            os.makedirs( dest_dir )
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(dest_dir):
                pass
            else: 
                bb.warn( "mkdir failed " + str(e) + "\n" )
                continue

        try:
            shutil.copyfile( abs_path, dest_path )
        except shutil.Error as e:
            bb.warn( str(e) + "\n" )
        except IOError as e:
            bb.warn( str(e) + "\n" )
    
    tar_file = os.path.join( info['workdir'], info['pn'] + ".tar.gz" )
    with tarfile.open( tar_file, "w:gz" ) as tar:
        tar.add( info['spdxdir'], arcname=os.path.basename(info['spdxdir']) )
    tar.close()
    
    return file_info, tar_file


def remove_dir_tree( dir_name ):
    import shutil
    try: 
        shutil.rmtree( dir_name )
    except:
        pass

def remove_file( file_name ):
    try:
        os.remove( file_name )
    except OSError as e:
        pass

def list_files( dir ):
    for root, subFolders, files in os.walk( dir ):
        for f in files:
            rel_root = os.path.relpath( root, dir )
            yield rel_root, f
    return

def hash_file( file_name ):
    f = open( file_name, 'rb' )
    try:
        data_string = f.read()
    finally:
        f.close()
    sha1 = hash_string( data_string )
    return sha1

def hash_string( data ):
    import hashlib
    sha1 = hashlib.sha1()
    sha1.update( data )
    return sha1.hexdigest()

def parse_foss_scan( tar_file ):
    import string, re
    import subprocess
    
    copyright_flag = 'true'
    foss_server = "https://foss-spdx-dev.ist.unomaha.edu"\
        + "/?mod=spdx_license_once&noCopyright=" + copyright_flag
    foss_flags = ["wget", "-qO", "-", "--no-check-certificate", 
        "--timeout=0", "--post-file=" + tar_file, foss_server]
    p = subprocess.Popen(foss_flags, stdout=subprocess.PIPE)
    foss_output, foss_error = p.communicate()
    
    records = []
    records = re.findall('FileName:.*?</text>', foss_output, re.S)

    file_info = {}
    for rec in records:
        rec = string.replace( rec, '\r', '' )
        chksum = re.findall( 'FileChecksum: SHA1: (.*)\n', rec)[0]
        file_info[chksum] = {}
        file_info[chksum]['FileCopyrightText'] = re.findall( 'FileCopyrightText: ' 
            + '(.*?</text>)', rec, re.S )[0]
        fields = ['FileType','LicenseConcluded',
            'LicenseInfoInFile','FileName']
        for field in fields:
            file_info[chksum][field] = re.findall(field + ': (.*)', rec)[0]

    return file_info

def create_spdx_doc( local_file_info, foss_file_info ):
    import json
    spdx_doc = []
    for chksum, lic_info in foss_file_info.iteritems():
        file_block = []
        if chksum in local_file_info:
            file_block.append( "FileName: " + local_file_info[chksum]['FileName'] )
            file_block.append( "FileType: " + lic_info['FileType'] )
            file_block.append( "FileChecksum: SHA1: " + chksum )
            file_block.append( "LicenseInfoInFile: " 
                + lic_info['LicenseInfoInFile'] )
            file_block.append( "LicenseConcluded: " 
                + lic_info['LicenseConcluded'] )
            file_block.append( "FileCopyrightText: " 
                + lic_info['FileCopyrightText'] )
            spdx_doc.append( '\n'.join( file_block ) + '\n\n' )
        else:
            bb.warn(lic_info['FileName'] + " : " + chksum 
                + " : is not in the local file info: " 
                + json.dumps(lic_info,indent=1))
    return spdx_doc

def get_ver_code( chksums ):
    chksums.sort()
    ver_code_string = ''.join( chksums ).lower()
    ver_code = hash_string( ver_code_string )
    return ver_code

def get_header_info( info, local, foss ):
    """
        Put together the header SPDX information. 
        Eventually this needs to become a lot less 
        of a hardcoded thing. 
    """
    from datetime import datetime
    import os
    head = []

    spdx_verification_code = get_ver_code( local.keys() )
    package_checksum = hash_file( info['tar_file'] )
    DEFAULT = "NOASSERTION"

    ## document level information
    head.append("SPDXVersion: " + info['spdx_version'])
    head.append("DataLicense: " + info['data_license'])
    head.append("DocumentComment: <text>SPDX for "
        + info['pn'] + " version " + info['pv'] + "</text>")
    head.append("")

    ## Creator information
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    head.append("## Creation Information")
    head.append("Creator: fossology-spdx")
    head.append("Created: " + now)
    head.append("CreatorComment: <text>UNO</text>")
    head.append("")

    ## package level information
    head.append("## Package Information")
    head.append("PackageName: " + info['pn'])
    head.append("PackageVersion: " + info['pv'])
    head.append("PackageDownloadLocation: " + info['src_uri'].split()[0])
    head.append("PackageSummary: <text></text>")
    head.append("PackageFileName: " + os.path.basename(info['tar_file']))
    head.append("PackageSupplier: Person:" + DEFAULT)
    head.append("PackageOriginator: Person:" + DEFAULT)
    head.append("PackageChecksum: SHA1: " + package_checksum)
    head.append("PackageVerificationCode: " + spdx_verification_code)
    head.append("PackageDescription: <text>" + info['pn']
        + " version " + info['pv'] + "</text>")
    head.append("")
    head.append("PackageCopyrightText: <text>" + DEFAULT + "</text>")
    head.append("")
    head.append("PackageLicenseDeclared: " + DEFAULT)
    head.append("PackageLicenseConcluded: " + DEFAULT)
    head.append("PackageLicenseInfoFromFiles: " + DEFAULT)
    head.append("")
    
    ## header for file level
    head.append("## File Information")
    head.append("")

    return '\n'.join(head)
