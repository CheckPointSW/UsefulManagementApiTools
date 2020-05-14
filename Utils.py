import datetime
import time
from cpapi import APIClient, APIClientArgs

# Script running time in seconds
DATETIME_NOW = datetime.datetime.now().replace(microsecond=0)
DATETIME_NOW_SEC = int(round(time.mktime(DATETIME_NOW.timetuple())))
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATETIME_NOW_STR = datetime.datetime.fromtimestamp(DATETIME_NOW_SEC).strftime(DATETIME_FORMAT)
log_file = None


# Print message with time description
def print_msg(msg):
    global log_file
    log_file.write("[{}] {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg))


# Exit and discard if the API-call failed & print error message
def exit_failure(error_msg, response, client=None):
    if response.success is False:
        if client:
            client.api_call("discard")
        print_msg(error_msg + " Error: {}".format(response.error_message))
        exit(1)


def login(user_args, client):
    session_details = {"session-name": user_args.session_name, "session-description": user_args.session_description}
    if user_args.root is not None and user_args.root.lower() == 'true':
        if user_args.management == '127.0.0.1':
            login_res = client.login_as_root(domain=user_args.domain,
                                             payload=session_details)
        else:
            print_msg("Error: Command contains ambiguous parameters. "
                      "Management server remote ip is unexpected when logging in as root.")
            exit(1)
    else:
        login_res = client.login(user_args.username, user_args.password, domain=user_args.domain,
                                 payload=session_details)

    exit_failure("Failed to login.", login_res)