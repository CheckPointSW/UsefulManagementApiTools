import argparse
import os

from cpapi import APIClient, APIClientArgs

import Utils


def populate_parser():
    parser = argparse.ArgumentParser(description="Add tags to objects.")
    parser.add_argument("--username", "-u", required=False, default=os.getenv('MGMT_CLI_USER'),
                        help="The management administrator's user name.\nEnvironment variable: MGMT_CLI_USER")
    parser.add_argument("--password", "-p", required=False,
                        help="The management administrator's password.\nEnvironment variable: MGMT_CLI_PASSWORD")
    parser.add_argument("--management", "-m", required=False, default=os.getenv('MGMT_CLI_MANAGEMENT', "127.0.0.1"),
                        help="The management server's IP address (In the case of a Multi-Domain Environment, "
                             "use the IP address of the MDS domain).\nDefault: 127.0.0.1\nEnvironment variable: "
                             "MGMT_CLI_MANAGEMENT")
    parser.add_argument("--port", "--server-port", required=False, default=os.getenv('MGMT_CLI_PORT', 443),
                        help="The port of the management server\nDefault: 443\nEnvironment variable: MGMT_CLI_PORT")
    parser.add_argument("--domain", "-d", required=False, default=os.getenv('MGMT_CLI_DOMAIN'),
                        help="The name, uid or IP-address of the management domain\n"
                             "Environment variable: MGMT_CLI_DOMAIN")
    parser.add_argument('--root', '-r', choices=['true', 'false'],
                        help='\b{%(choices)s}\nLogin as root. When running on the management server, '
                             'use this flag with value set to \'true\' to login as Super User administrator.',
                        metavar=" \b\b")
    parser.add_argument('--session-name', help='\nSession unique name. Default {add_tag}',
                        default="add_tag", metavar="")
    parser.add_argument('--session-description', help='Session description. Default {Current time}',
                        default=Utils.DATETIME_NOW_STR, metavar="")
    parser.add_argument('--partial-name', '-pn', required=False,
                        help="Add tag to objects shown in object explorer by the provided partial-name. "
                             "\nThis field required in case of using \'--only-used\' flag")
    parser.add_argument('--mode', '-md', default='unused', choices=['used', 'unused', 'all'],
                        help="Use this flag with value set to \'used\' to update only used objects, "
                             "\'unused\' to update only unused objects or \'all\' to ignore the filter." +
                             " \nDefault: \'unused\'.")
    parser.add_argument('--tag', '-t', required=True, help="Name of the tag to add.")
    return parser.parse_args()


def is_in_use(client, uid):
    res = client.api_call("where-used", {"uid": uid})
    Utils.exit_failure("Failed to get usages of " + uid, res, client)
    if int(res.data.get("used-directly").get("total")) > 0:
        return True
    else:
        return False


def main():
    user_args = populate_parser()
    Utils.log_file = open(os.path.dirname(os.path.abspath(__file__)) + os.sep + 'add_tag' +
                          (user_args.domain if user_args.domain else "") + '_' +
                          str(Utils.DATETIME_NOW_SEC) + '.txt', 'w+')
    client_args = APIClientArgs(server=user_args.management, port=user_args.port)

    with APIClient(client_args) as client:
        # The API client, would look for the server's certificate SHA1 fingerprint in a file.
        # If the fingerprint is not found on the file, it will ask the user if he accepts the server's fingerprint.
        # In case the user does not accept the fingerprint, exit the program.
        if client.check_fingerprint() is False:
            Utils.print_msg("Could not get the server's fingerprint - Check connectivity with the server.")
            exit(1)

        Utils.login(user_args, client)

        if user_args.partial_name:
            result = client.api_query(command="show-objects", payload={"in": ["name", user_args.partial_name]})
            objects = result.data
        else:
            if user_args.mode.lower() != "unused":
                print("Can not use \'--mode\' flag set to \'used\' or \'all\' without \'partial-name\'")
                client.api_call("discard")
                exit(1)
            result = client.api_query(command="show-unused-objects", payload={})
            objects = result.data
            pass

        i = 0
        for candidate_object in objects:
            object_type = candidate_object.get("type")
            uid = candidate_object.get("uid")

            if user_args.partial_name and user_args.mode:
                if user_args.mode.lower() == "used":
                    if is_in_use(client, uid) is False:
                        Utils.print_msg("WARNING: Object not in use " + uid)
                        continue
                elif user_args.mode.lower() == "unused":
                    if is_in_use(client, uid) is True:
                        Utils.print_msg("WARNING: Object in use " + uid)
                        continue

            res = client.api_call("set-" + object_type, {"uid": uid, "tags": {"add": user_args.tag}})

            if res.success is False:
                if res.error_message == "Requested API command: [set-" + object_type + "] not found":
                    Utils.print_msg("WARNING: Object of type \'" + object_type + "\' is not supported. " +
                                    "If necessary add tag manually to \'" + candidate_object.get("name") + "\'.")
                    print("WARNING: Object of type " + object_type + " is not supported. " +
                          "If necessary add tag manually to " + candidate_object.get("name") + ".")
                    continue
                elif "Object " + uid + " is read-only." in res.error_message:
                    Utils.print_msg("WARNING: \'" + candidate_object.get("name") + "\' of type \'" + object_type +
                                    "\' is read only object.")
                    print("WARNING: \'" + candidate_object.get("name") + "\' of type \'" + object_type +
                          "\' is read only object.")
                    continue
                elif "cannot be locked because it belongs to domain" in res.error_message:
                    Utils.print_msg("WARNING: \'" + candidate_object.get("name") + "\' of type \'" + object_type +
                                    "\' is from other domain.")
                    print("WARNING: \'" + candidate_object.get("name") + "\' of type \'" + object_type +
                          "\' is from other domain.")
                    continue
                else:
                    Utils.exit_failure("Fail to set " + object_type + " with uid " + uid, res, client)
            else:
                Utils.print_msg("tag was added successfully to \'" + candidate_object.get("name") + "\'")
                print("tag was added successfully to \'" + candidate_object.get("name") + "\'")
            i = i + 1
            if i % 50 == 0:
                res = client.api_call("publish")
                Utils.exit_failure("Publish operation failed ", res, client)

        res = client.api_call("publish")
        Utils.exit_failure("Publish operation failed ", res, client)
    Utils.print_msg("Script finished successfully")
    Utils.log_file.close()


if __name__ == "__main__":
    main()
