import subprocess

'''
该模块用于使用SNMP获取交换机信息，调用了snmpwalk.exe，若是linux系统，修改一下Popen后面的代码即可。
用法：snmp(ip, info)
ip为交换机的ip地址，如"172.16.101.4"
info为字符串，如"cpu_load_5min"、"memory_used_rate"、"total_memory"等等，具体看下面的代码。
返回字符串。
'''

# I don't import SNMP library because none of them can run well in windows.
# windows可用,linux需作修改。
# 待改进：不同型号的设备配对不同的OID，改进该模块性能（速度）。
# 交换机型号：E152B
SNMP_TIMEOUT = "0.5"
SNMP_RETRY_TIMES = "1"
SNMP_VER = "2c"
SNMP_COMMUNITY = "123456"
SNMP_OID_cpu_load_5min = "1.3.6.1.4.1.2011.6.1.1.1.4.0"
SNMP_OID_memory_used_rate = "1.3.6.1.4.1.25506.2.6.1.1.1.1.8.82"
SNMP_OID_total_memory = "1.3.6.1.4.1.25506.2.6.1.1.1.1.10.82"
SNMP_OID_used_memory = "1.3.6.1.4.1.25506.2.6.1.1.1.1.11.2"
SNMP_OID_fan = ""
SNMP_OID_temperature = "1.3.6.1.4.1.2011.5.25.31.1.1.1.5"


def snmp(ip, info):
    b = ""
    if info == "test":  # ip="demo.snmplabs.com"
        b = subprocess.Popen(
            ["bin\snmpwalk", "-O", "qv", "-t", "5", "-r", "2", "-v", SNMP_VER, "-c", "index", ip,
             "1.3.6.1.4.1.20408.999.1.1.1"], bufsize=0, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        return b.stdout.read().decode('utf-8')
    if info == "cpu_load_5min":
        b = subprocess.Popen(
            ["bin\snmpwalk", "-O", "qv", "-t", SNMP_TIMEOUT, "-r", SNMP_RETRY_TIMES, "-v", SNMP_VER, "-c",
             SNMP_COMMUNITY, ip, SNMP_OID_cpu_load_5min], shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    if info == "memory_used_rate":
        b = subprocess.Popen(
            ["bin\snmpwalk", "-O", "qv", "-t", SNMP_TIMEOUT, "-r", SNMP_RETRY_TIMES, "-v", SNMP_VER, "-c",
             SNMP_COMMUNITY, ip, SNMP_OID_memory_used_rate], shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    if info == "total_memory":
        b = subprocess.Popen(
            ["bin\snmpwalk", "-O", "qv", "-t", SNMP_TIMEOUT, "-r", SNMP_RETRY_TIMES, "-v", SNMP_VER, "-c",
             SNMP_COMMUNITY, ip, SNMP_OID_total_memory], shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    if info == "used_memory":
        b = subprocess.Popen(
            ["bin\snmpwalk", "-O", "qv", "-t", SNMP_TIMEOUT, "-r", SNMP_RETRY_TIMES, "-v", SNMP_VER, "-c",
             SNMP_COMMUNITY, ip, SNMP_OID_used_memory], shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    return b.stdout.read().decode('utf-8')[:-2]  # 去掉回车和换行符


if __name__ == '__main__':
    a = snmp('demo.snmplabs.com', 'test')
    print(a)  # 应该返回 "/usr/snmpsim/data/1.3.6.1.6.1.1.0/127.0.0.1.snmprec"

'''
USAGE: snmpwalk [OPTIONS] AGENT [OID]

  Version:  5.7
  Web:      http://www.net-snmp.org/
  Email:    net-snmp-coders@lists.sourceforge.net

OPTIONS:
  -h, --help            display this help message
  -H                    display configuration file directives understood
  -v 1|2c|3             specifies SNMP version to use
  -V, --version         display package version number
SNMP Version 1 or 2c specific
  -c COMMUNITY          set the community string
SNMP Version 3 specific
  -a PROTOCOL           set authentication protocol (MD5|SHA)
  -A PASSPHRASE         set authentication protocol pass phrase
  -e ENGINE-ID          set security engine ID (e.g. 800000020109840301)
  -E ENGINE-ID          set context engine ID (e.g. 800000020109840301)
  -l LEVEL              set security level (noAuthNoPriv|authNoPriv|authPriv)
  -n CONTEXT            set context name (e.g. bridge1)
  -u USER-NAME          set security name (e.g. bert)
  -x PROTOCOL           set privacy protocol (DES)
  -X PASSPHRASE         set privacy protocol pass phrase
  -Z BOOTS,TIME         set destination engine boots/time
General communication options
  -r RETRIES            set the number of retries
  -t TIMEOUT            set the request timeout (in seconds)
Debugging
  -d                    dump input/output packets in hexadecimal
  -D[TOKEN[,...]]       turn on debugging output for the specified TOKENs
                           (ALL gives extremely verbose debugging output)
General options
  -m MIB[:...]          load given list of MIBs (ALL loads everything)
  -M DIR[:...]          look in given list of directories for MIBs
    (default: c:/usr/share/snmp/mibs)
  -P MIBOPTS            Toggle various defaults controlling MIB parsing:
                          u:  allow the use of underlines in MIB symbols
                          c:  disallow the use of "--" to terminate comments
                          d:  save the DESCRIPTIONs of the MIB objects
                          e:  disable errors when MIB symbols conflict
                          w:  enable warnings when MIB symbols conflict
                          W:  enable detailed warnings when MIB symbols conflict
                          R:  replace MIB symbols from latest module
  -O OUTOPTS            Toggle various defaults controlling output display:
                          0:  print leading 0 for single-digit hex characters
                          a:  print all strings in ascii format
                          b:  do not break OID indexes down
                          e:  print enums numerically
                          E:  escape quotes in string indices
                          f:  print full OIDs on output
                          n:  print OIDs numerically
                          q:  quick print for easier parsing
                          Q:  quick print with equal-signs
                          s:  print only last symbolic element of OID
                          S:  print MIB module-id plus last element
                          t:  print timeticks unparsed as numeric integers
                          T:  print human-readable text along with hex strings
                          u:  print OIDs using UCD-style prefix suppression
                          U:  don't print units
                          v:  print values only (not OID = value)
                          x:  print all strings in hex format
                          X:  extended index format
  -I INOPTS             Toggle various defaults controlling input parsing:
                          b:  do best/regex matching to find a MIB node
                          h:  don't apply DISPLAY-HINTs
                          r:  do not check values for range/type legality
                          R:  do random access to OID labels
                          u:  top-level OIDs must have '.' prefix (UCD-style)
                          s SUFFIX:  Append all textual OIDs with SUFFIX before parsing
                          S PREFIX:  Prepend all textual OIDs with PREFIX before parsing
  -L LOGOPTS            Toggle various defaults controlling logging:
                          e:           log to standard error
                          o:           log to standard output
                          n:           don't log at all
                          f file:      log to the specified file
                          s facility:  log to syslog (via the specified facility)

                          (variants)
                          [EON] pri:   log to standard error, output or /dev/null for level 'pri' and above
                          [EON] p1-p2: log to standard error, output or /dev/null for levels 'p1' to 'p2'
                          [FS] pri token:    log to file/syslog for level 'pri' and above
                          [FS] p1-p2 token:  log to file/syslog for levels 'p1' to 'p2'
  -C APPOPTS            Set various application specific behaviours:
                          p:  print the number of variables found
                          i:  include given OID in the search range
                          I:  don't include the given OID, even if no results are returned
                          c:  do not check returned OIDs are increasing
                          t:  Display wall-clock time to complete the walk
                          T:  Display wall-clock time to complete each request
                          E {OID}:  End the walk at the specified OID
'''
