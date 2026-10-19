#!/bin/bash
# fetch_many.sh <outdir> name=hf_tail.png ...   (tail = the result_url file name)
D=$1; shift; B=https://d8j0ntlcm91z4.cloudfront.net/user_3JVmaIlSsymA3xsWh0PuqMSMLE9
for a in "$@"; do "$(dirname "$0")/fetch.sh" "$D/${a%%=*}.jpg" "$B/${a#*=}"; done
