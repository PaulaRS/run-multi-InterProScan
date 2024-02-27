__author__ = "Paula Ramos-Silva"
__dateCreated__ = "02-08-2022"
__dateModified__ = "27-02-2024"

"""
Adapted from:
https://www.ebi.ac.uk/seqdb/confluence/display/JDSAT/InterProScan+5+Help+and+Documentation#InterProScan5HelpandDocumentation-RESTAPI
InterProScan 5 (REST) Python client using urllib2 and xmltramp (http://www.aaronsw.com/2002/xmltramp/).

Usage:
python iprscan5_urllib2.py [options...] --email <email> --sequence <multi_protein_fasta_file>

Note:
EMBL-EBI Web Services asks to submit tool jobs in batches of no more than 30 at a time and not to 
submit more until the results and processing is complete. Please ensure that a valid email address is provided. 
Excessive usage of a particular resource will be dealt with in accordance with EMBL-EBI's Terms of Use. 

Tested with:
Python 2.7 (macOS Monterey 12.3.1)
"""
# Load libraries
import os
import platform
import re
import sys
import time
import urllib
import urllib2
from optparse import OptionParser
from xmltramp2 import xmltramp

# BaseURL for service
baseUrl = 'https://www.ebi.ac.uk/Tools/services/rest/iprscan5'

# Set interval for checking status
checkInterval = 10
# Output level
outputLevel = 1
# Debug level
debugLevel = 0
# Number of option arguments.
numOpts = len(sys.argv)

# Usage message
usage = "Usage: python iprscan5_urllib2.py [options...] --email <email> --sequence <multi_protein_fasta_file>"
description = """Identify protein family, domain and signal signatures in a 
protein sequence using InterProScan."""
epilog = """For further information about the InterProScan 5 (REST) web service, https://www.ebi.ac.uk/interpro/"""
version = "$Id: iprscan5_urllib2.py 2809 2022-11-21 16:34:25Z uludag $"
# Process command-line options
parser = OptionParser(usage=usage, description=description, epilog=epilog, version=version)
# Commands
parser.add_option('--email', help='e-mail address')
parser.add_option('--sequence', help='input sequence file name')
# Tool specific options
parser.add_option('--appl', help='signature methods to use, see --paramDetail appl')
parser.add_option('--crc', action="store_true", help='enable InterProScan Matches look-up (ignored)')
parser.add_option('--nocrc', action="store_true", help='disable InterProScan Matches look-up (ignored)')
parser.add_option('--goterms', action="store_true", help='enable inclusion of GO terms')
parser.add_option('--nogoterms', action="store_true", help='disable inclusion of GO terms')
parser.add_option('--pathways', action="store_true", help='enable inclusion of pathway terms')
parser.add_option('--nopathways', action="store_true", help='disable inclusion of pathway terms')
# General options
parser.add_option('--title', help='job title')
parser.add_option('--outfile', help='file name for results')
parser.add_option('--outformat', help='output format for results')
parser.add_option('--async', action='store_true', help='asynchronous mode')
parser.add_option('--jobid', help='job identifier')
parser.add_option('--polljob', action="store_true", help='get job result')
parser.add_option('--status', action="store_true", help='get job status')
parser.add_option('--resultTypes', action='store_true', help='get result types')
parser.add_option('--params', action='store_true', help='list input parameters')
parser.add_option('--paramDetail', help='get details for parameter')
parser.add_option('--quiet', action='store_true', help='decrease output level')
parser.add_option('--verbose', action='store_true', help='increase output level')
parser.add_option('--baseURL', default=baseUrl, help='Base URL for service')
parser.add_option('--debugLevel', type='int', default=debugLevel, help='debug output level')

(options, args) = parser.parse_args()

# Increase output level
if options.verbose:
    outputLevel += 1

# Decrease output level
if options.quiet:
    outputLevel -= 1

# Debug level
if options.debugLevel:
    debugLevel = options.debugLevel


# Debug print
def print_debug_message(function_name, message, level):
    if level <= debugLevel:
        print >> sys.stderr, '[' + function_name + '] ' + message


# User-agent for request (see RFC2616).
def get_user_agent():
    print_debug_message('getUserAgent', 'Begin', 11)
    # Agent string for urllib2 library.
    urllib_agent = 'Python-urllib/%s' % urllib2.__version__
    client_revision = '$Revision: 2809 $'
    client_version = '0'
    if len(client_revision) > 11:
        client_version = client_revision[11:-2]
    # Prepend client specific agent string.
    user_agent = 'EBI-Sample-Client/%s (%s; Python %s; %s) %s' % (
        client_version, os.path.basename(__file__),
        platform.python_version(), platform.system(),
        urllib_agent
    )
    print_debug_message('getUserAgent', 'user_agent: ' + user_agent, 12)
    print_debug_message('getUserAgent', 'End', 11)
    return user_agent


# Wrapper for a REST (HTTP GET) request
def rest_request(url):
    print_debug_message('restRequest', 'Begin', 11)
    print_debug_message('restRequest', 'url: ' + url, 11)
    # Errors are indicated by HTTP status codes.
    try:
        # Set the User-agent.
        user_agent = get_user_agent()
        http_headers = {'User-Agent': user_agent}
        req = urllib2.Request(url, None, http_headers)
        # Make the request (HTTP GET).
        req_h = urllib2.urlopen(req)
        result = req_h.read()
        req_h.close()
    # Errors are indicated by HTTP status codes.
    except urllib2.HTTPError, ex:
        # Trap exception and output the document to get error message.
        print >> sys.stderr, ex.read()
        raise
    print_debug_message('restRequest', 'End', 11)
    return result


# Get input parameters list
def service_get_parameters():
    print_debug_message('service_get_parameters', 'Begin', 1)
    request_url = baseUrl + '/parameters'
    print_debug_message('service_get_parameters', 'request_url: ' + request_url, 2)
    xml_doc = rest_request(request_url)
    doc = xmltramp.parse(xml_doc)
    print_debug_message('service_get_parameters', 'End', 1)
    return doc['id':]


# Print list of parameters
def print_get_parameters():
    print_debug_message('print_get_parameters', 'Begin', 1)
    id_list = service_get_parameters()
    for ID in id_list:
        print ID
    print_debug_message('print_get_parameters', 'End', 1)


# Get input parameter information
def service_get_parameter_details(param_name):
    print_debug_message('service_get_parameter_details', 'Begin', 1)
    print_debug_message('service_get_parameter_details', 'param_name: ' + param_name, 2)
    request_url = baseUrl + '/parameter_details/' + param_name
    print_debug_message('service_get_parameter_details', 'request_url: ' + request_url, 2)
    xml_doc = rest_request(request_url)
    doc = xmltramp.parse(xml_doc)
    print_debug_message('service_get_parameter_details', 'End', 1)
    return doc


# Print description of a parameter
def print_get_parameter_details(param_name):
    print_debug_message('print_get_parameter_details', 'Begin', 1)
    doc = service_get_parameter_details(param_name)
    print str(doc.name) + "\t" + str(doc.type)
    print doc.description
    for value in doc.values:
        print value.value,
        if str(value.defaultValue) == 'true':
            print 'default',
        print
        print "\t" + str(value.label)
        if hasattr(value, 'properties'):
            for wsProperty in value.properties:
                print "\t" + str(wsProperty.key) + "\t" + str(wsProperty.value)
    # print doc
    print_debug_message('print_get_parameter_details', 'End', 1)


# Submit job
def service_run(email, title, parameters):
    print_debug_message('service_run', 'Begin', 1)
    # Insert e-mail and title into parameters
    parameters['email'] = email
    if title:
        parameters['title'] = title
    request_url = baseUrl + '/run/'
    print_debug_message('service_run', 'request_url: ' + request_url, 2)
    # Signature methods requires special handling (list)
    appl_data = ''
    if 'appl' in parameters:
        # So extract from parameters
        appl_list = parameters['appl']
        del parameters['appl']
        # Build the method data options
        for appl in appl_list:
            appl_data += '&appl=' + appl
    # Get the data for the other options
    request_data = urllib.urlencode(parameters)
    # Concatenate the two parts.
    request_data += appl_data
    print_debug_message('service_run', 'request_data: ' + request_data, 2)
    # Errors are indicated by HTTP status codes.
    try:
        # Set the HTTP User-agent.
        user_agent = get_user_agent()
        http_headers = {'User-Agent': user_agent}
        req = urllib2.Request(request_url, None, http_headers)
        # Make the submission (HTTP POST).
        req_h = urllib2.urlopen(req, request_data)
        job_id = req_h.read()
        req_h.close()
    except urllib2.HTTPError, ex:
        # Trap exception and output the document to get error message.
        print >> sys.stderr, ex.read()
        raise
    print_debug_message('service_run', 'job_id: ' + job_id, 2)
    print_debug_message('service_run', 'End', 1)
    return job_id


# Get job status
def service_get_status(job_id):
    print_debug_message('service_get_status', 'Begin', 1)
    print_debug_message('service_get_status', 'job_id: ' + job_id, 2)
    request_url = baseUrl + '/status/' + job_id
    print_debug_message('service_get_status', 'request_url: ' + request_url, 2)
    status = rest_request(request_url)
    print_debug_message('service_get_status', 'status: ' + status, 2)
    print_debug_message('service_get_status', 'End', 1)
    return status


# Print the status of a job
def print_get_status(job_id):
    print_debug_message('print_get_status', 'Begin', 1)
    status = service_get_status(job_id)
    print status
    print_debug_message('print_get_status', 'End', 1)


# Get available result types for job
def service_get_result_types(job_id):
    print_debug_message('service_get_result_types', 'Begin', 1)
    print_debug_message('service_get_result_types', 'job_id: ' + job_id, 2)
    request_url = baseUrl + '/result_types/' + job_id
    print_debug_message('service_get_result_types', 'reques_url: ' + request_url, 2)
    xml_doc = rest_request(request_url)
    doc = xmltramp.parse(xml_doc)
    print_debug_message('service_get_result_types', 'End', 1)
    return doc['type':]


# Print list of available result types for a job.
def print_get_result_types(job_id):
    print_debug_message('print_get_result_types', 'Begin', 1)
    result_type_list = service_get_result_types(job_id)
    for resultType in result_type_list:
        print resultType['identifier']
        if hasattr(resultType, 'label'):
            print "\t", resultType['label']
        if hasattr(resultType, 'description'):
            print "\t", resultType['description']
        if hasattr(resultType, 'mediaType'):
            print "\t", resultType['mediaType']
        if hasattr(resultType, 'fileSuffix'):
            print "\t", resultType['fileSuffix']
    print_debug_message('print_get_result_types', 'End', 1)


# Get result
def service_get_result(job_id, type_):
    print_debug_message('service_get_result', 'Begin', 1)
    print_debug_message('service_get_result', 'job_id: ' + job_id, 2)
    print_debug_message('service_get_result', 'type_: ' + type_, 2)
    request_url = baseUrl + '/result/' + job_id + '/' + type_
    result = rest_request(request_url)
    print_debug_message('service_get_result', 'End', 1)
    return result


# Client-side poll
def client_poll(job_id):
    print_debug_message('client_poll', 'Begin', 1)
    result = 'PENDING'
    while result == 'RUNNING' or result == 'PENDING':
        result = service_get_status(job_id)
        print >> sys.stderr, result
        if result == 'RUNNING' or result == 'PENDING':
            time.sleep(checkInterval)
    print_debug_message('client_poll', 'End', 1)


# Get result for a jobid
def get_result(job_id):
    print_debug_message('get_result', 'Begin', 1)
    print_debug_message('get_result', 'job_id: ' + job_id, 1)
    # Check status and wait if necessary
    client_poll(job_id)
    # Get available result types
    result_types = service_get_result_types(job_id)
    for resultType in result_types:
        # Derive the filename for the result
        if options.outfile:
            filename = options.outfile + '.' + str(resultType['identifier']) + '.' + str(resultType['fileSuffix'])
        else:
            filename = job_id + '.' + str(resultType['identifier']) + '.' + str(resultType['fileSuffix'])
        # Write a result file
        if not options.outformat or options.outformat == str(resultType['identifier']):
            # Get the result
            result = service_get_result(job_id, str(resultType['identifier']))
            fh = open(filename, 'w')
            fh.write(result)
            fh.close()
            print filename
    print_debug_message('get_result', 'End', 1)


# Read a file
def read_file(filename):
    print_debug_message('read_file', 'Begin', 1)
    fh = open(filename, 'r')
    data = fh.read()
    fh.close()
    print_debug_message('read_file', 'End', 1)
    return data


# No options... print help.
if numOpts < 2:
    parser.print_help()
# List parameters
elif options.params:
    print_get_parameters()
# Get parameter details
elif options.paramDetail:
    print_get_parameter_details(options.paramDetail)
# Submit job
elif options.email and not options.jobid:
    params = {}
    if len(args) > 0:
        if os.access(args[0], os.R_OK):  # Read file into content
            params['sequence'] = read_file(args[0])
        else:  # Argument is a sequence id
            params['sequence'] = args[0]
    elif options.sequence:  # Specified via option
        if os.access(options.sequence, os.R_OK):  # Read file into content
            params['sequence'] = read_file(options.sequence)
        else:  # Argument is a sequence id
            params['sequence'] = options.sequence
    # Map flag options to boolean values.
    # if options.crc:
    #    params['crc'] = True
    # elif options.nocrc:
    #    params['crc'] = False
    if options.goterms:
        params['goterms'] = True
    elif options.nogoterms:
        params['goterms'] = False
    if options.pathways:
        params['pathways'] = True
    elif options.nopathways:
        params['pathways'] = False
    # Add the other options (if defined)
    if options.appl:
        params['appl'] = re.split('[ \t\n,;]+', options.appl)

    # Submit the job
    jobid = service_run(options.email, options.title, params)
    if options.async:  # Async mode
        print jobid
    else:  # Sync mode
        print >> sys.stderr, jobid
        time.sleep(5)
        get_result(jobid)
# Get job status
elif options.status and options.jobid:
    print_get_status(options.jobid)
# List result types for job
elif options.resultTypes and options.jobid:
    print_get_result_types(options.jobid)
# Get results for job
elif options.polljob and options.jobid:
    get_result(options.jobid)
else:
    print >> sys.stderr, 'Error: unrecognised argument combination'
    parser.print_help()
