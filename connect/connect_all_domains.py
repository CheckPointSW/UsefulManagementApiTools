import argparse
import os
import ssl
import subprocess
import time

from cpapi import APIClient, APIClientArgs
import http.client
import json
import logging
import sys
from logging.handlers import RotatingFileHandler

CURL_CLI = '$MDS_FWDIR/bin/curl_cli'

CONSENT_MESSAGE = "I wish to connect my Self-Hosted Security Management environment and Security Gateways to the" \
                  " Infinity Portal. These will share with Check Point information which may include personal data and" \
                  " which will be processed per Check Point’s Privacy Policy.\n" \
                  "I understand that when connecting multiple Security Managements, data may be shared between them."

DEFAULT_API_PORT = 443
LOCAL_HOST_IP = "127.0.0.1"
LOCAL_HOST = "localhost"
SYSTEM_DATA = "System Data"


CI_URL_MAP = {
    "ap": "cloudinfra-gw.ap.portal.checkpoint.com",
    "us": "cloudinfra-gw-us.portal.checkpoint.com",
    "eu": "cloudinfra-gw.portal.checkpoint.com",
    "uae": "cloudinfra-gw.ae.portal.checkpoint.com",
    "in": "cloudinfra-gw.in.portal.checkpoint.com"
}


def make_http_request(method, endpoint, headers, data=None):
    if server == LOCAL_HOST_IP or server == LOCAL_HOST:
        return make_http_request_from_server(method, endpoint, headers, data)
    return make_http_request_from_remote(method, endpoint, headers, data)


def make_http_request_from_remote(method, endpoint, headers, data=None):
    conn = http.client.HTTPSConnection(ci_url)
    conn.request(method, endpoint, body=data, headers=headers)
    response = conn.getresponse()
    status_code = response.status
    content = response.read().decode()
    conn.close()

    return status_code, content


def make_http_request_from_server(method, endpoint, headers, data=None):
    command = CURL_CLI + " --cacert $CPDIR/conf/ca-bundle-public-cloud.crt -w \"\\nCODE:%{http_code}\\n\""
    command += f" -X {method} https://{ci_url}{endpoint}"
    for key, value in headers.items():
        command += f" -H '{key}: {value}'"
    command += f" -d '{data}'"
    if proxy and proxy_port:
        command += f" -x http://{proxy}:{proxy_port}"

    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    p.wait()
    if p.returncode != 0:
        logger.error("Failed to run command {}, failure reason is {} ".format(command, err))
    logger.debug("json_string is {} ".format(output))
    try:
        json_temp = output.decode("utf-8")
        code = json_temp.split("CODE:")[1]
        logger.info("Status code: " + code)
        json_temp = json_temp.strip("\\nCODE:"+code+"\\n")
        return int(code.strip()), json_temp

    except ValueError as ex:
        logger.error(output)


def add_om_prem(jwt, domain):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(jwt),
        'User-Agent': 'connect-all-domains'
    }

    data = json.dumps({
        "name": domain,
        "isCloudMgmtService": False,
        "consent": True
    })

    code, content = make_http_request("POST", "/app/maas/api/v2/environments/", headers, data)

    if code == 200:
        logger.info(f'Successfully added MGMT instance of domain: {domain}')
        content = json.loads(content)
        return content['data']['authToken']['token']
    else:
        logger.error(f'Failed to add MGMT instance for domain {domain}')
        return None


def get_jwt():
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'connect-all-domains'
    }

    data = json.dumps({
        "clientId": client_id,
        "accessKey": access_key
    })

    code, content = make_http_request("POST", "/auth/external", headers, data)
    if code == 200 or (code == 302 and proxy and proxy_port):
        logger.info("Successfully created external jwt from given keys")
        content = json.loads(content)
        return content['data']['token']
    else:
        logger.error("Failed to create external jwt from given keys with the following error: {}".format(content))
        exit(1)


def logger_configuration():
    log_backup_count = 3
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(script_dir, 'connect_all_domains.log')
    log_max_bytes = 10_000_000_000
    log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    logging_handler = RotatingFileHandler(log_file, maxBytes=log_max_bytes, backupCount=log_backup_count)
    logging_handler.setFormatter(log_formatter)
    logging_handler.setLevel(logging.DEBUG)
    logger = logging.getLogger('root')
    logger.setLevel(logging.INFO)
    logger.addHandler(logging_handler)

    return logger


def user_consent():
    print("Connect my Self-hosted Security Management environment and Security Gateways to Infinity")
    print(CONSENT_MESSAGE)
    consent = input("Do you agree? y/n: ")
    logger.info("User must agree to the following message:\n {}".format(CONSENT_MESSAGE))
    logger.info("User's response: {}".format(consent))
    if consent.lower() != "y":
        raise Exception("Consent must be given in order to run this script")


def get_args(args):
    if args:
        parser = argparse.ArgumentParser()
        parser.add_argument("--client_id", type=str, action="store", help="Client Id", dest="client_id", required=True)
        parser.add_argument("--access_key", type=str, action="store", help="Access Key", dest="access_key",
                            required=True)
        parser.add_argument("--region", type=str, action="store", help="Region", dest="region",
                            choices=['ap', 'us', 'eu', 'uae', 'in'], required=True)
        parser.add_argument("--server", type=str, action="store", help="Server IP address or hostname, must be given "
                                                                       "when running from remote", dest="server")
        parser.add_argument("--api_key", type=str, action="store",
                            help="Api-Key must be given when running from remote", dest="api_key")
        parser.add_argument("--api_port", type=str, action="store",
                            help="Api Port must be given if running from remote and it isn't the default value",
                            dest="api_port")
        parser.add_argument("--debug_file", type=str, action="store", help="Api calls debug file name", dest="debug_file")

        args = parser.parse_args()
        client_id = args.client_id
        access_key = args.access_key
        region = args.region
        server = args.server if args.server else LOCAL_HOST_IP
        api_key = args.api_key
        api_port = args.api_port
        debug_file = args.debug_file if args.debug_file else ""

        return client_id, access_key, region, server, api_key, api_port, debug_file

    else:
        logger.error("No arguments given")
        exit(1)


def login(domain):
    logger.info("Logging in to domain {} of server {}...".format(domain, server))
    payload = {"session-name": "connect all domains to infinity portal",
               "session-description": "connect all domains to infinity portal"}
    if api_key:
        login_res = api_client.login_with_api_key(api_key=api_key, domain=domain, payload=payload)
    else:
        login_res = api_client.login_as_root(domain=domain, payload=payload)
    if login_res.success is False:
        logger.error("Login failed:\n{}".format(login_res.error_message))
        if domain == SYSTEM_DATA:
            exit(1)
    return login_res.success


def get_proxy():
    proxy_reply = api_client.api_call("show-proxy")
    if proxy_reply.success is False:
        logger.error("Failed to get proxy data:\n{}".format(proxy_reply.error_message))
        api_client.api_call("logout", {})
        exit(1)
    if proxy_reply.data["enabled"]:
        return proxy_reply.data["address"], proxy_reply.data["port"]
    else:
        return None, None


def get_port():
    script_path = os.path.expandvars("$MDS_FWDIR/scripts/api_get_port.py")
    try:
        result = subprocess.run(['python3', script_path, '-f', 'json'], capture_output=True, text=True, check=True)
        json_data = json.loads(result.stdout)
        return int(json_data["external_port"])
    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    return DEFAULT_API_PORT


def get_domains():
    domains = api_client.api_query("show-domains")
    if domains.success is False:
        logger.error("Failed to get the domains data:\n{}".format(domains.error_message))
        api_client.api_call("logout", {})
        exit(1)
    return domains.data


def connect_cloud_services(domain, auth_token):
    res = login(domain)
    if res is False:
        return res
    connect_reply = api_client.api_call("connect-cloud-services", {"auth-token": auth_token})
    connected = False
    if connect_reply.success is False:
        logger.error(
            "Failed to run connect-cloud-services on domain {}:\n{}".format(domain, connect_reply.error_message))
        print("Failed to connect domain: {}".format(domain))
    else:
        logger.info("Successfully connected cloud services on domain {}".format(domain))
        print("Successfully connected domain: {}".format(domain))
        connected = True
    api_client.api_call("logout", {})
    return connected


if __name__ == "__main__":
    logger = logger_configuration()
    logger.info("=====================================================================================================")
    print("=====================================================================================================")
    user_consent()
    client_id, access_key, region, server, api_key, api_port, debug_file = get_args(sys.argv[1:])
    ci_url = CI_URL_MAP.get(region)
    api_client = APIClient(APIClientArgs(server=server, debug_file=debug_file))
    if server != LOCAL_HOST and server != LOCAL_HOST_IP:  # if running from remote
        api_port = int(api_port) if api_port else DEFAULT_API_PORT
    else:
        api_port = int(api_port) if api_port else get_port()
    api_client.set_port(api_port)
    api_client.user_agent = "connect-all-domains"
    logger.info("=====================================================================================================")

    login(SYSTEM_DATA)
    if server == LOCAL_HOST_IP or server == LOCAL_HOST:
        proxy, proxy_port = get_proxy()
    else:
        proxy = None
        proxy_port = None
    domains = get_domains()
    api_client.api_call("logout", {})

    jwt = get_jwt()

    successful_connections = []
    failed_connections = []

    for domain in domains:
        domain_name = domain["name"]
        logger.info("==========================================================")
        logger.info("Starting to connect-cloud-services on domain {}".format(domain_name))
        auth_token = add_om_prem(jwt, domain_name)
        if auth_token is None:
            failed_connections.append(domain_name)
            continue
        connect_success = connect_cloud_services(domain_name, auth_token)
        if connect_success:
            successful_connections.append(domain_name)
        else:
            failed_connections.append(domain_name)
        time.sleep(3)
    api_client.save_debug_data()
    logger.info("==========================================================\nScript finished")
    print("=====================================================================================================")
    if len(successful_connections) == len(domains):
        print("Successfully connected all domains")
        exit(0)
    if len(successful_connections) > 0:
        print("Successfully connected the following domains:")
        for name in successful_connections:
            print(name)
    if len(failed_connections) > 0:
        print("Failed to connect the following domains:")
        for name in failed_connections:
            print(name)
    exit(1)
