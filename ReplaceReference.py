import argparse
import json
import os

from cpapi import APIClient, APIClientArgs

import Utils


def populate_parser():
    parser = argparse.ArgumentParser(
        description="replace references")
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
    parser.add_argument('--session-name', help='\nSession unique name. Default {replace_references}',
                        default="replace_references", metavar="")
    parser.add_argument('--session-description', help='Session description. Default {Current time}',
                        default=Utils.DATETIME_NOW_STR, metavar="")
    parser.add_argument('--original-reference', '-o', required=True, help="replace references of given object name.")
    parser.add_argument('--new-reference', '-n', required=True, help="use this prefix to fine the new objects")

    return parser.parse_args()


def get_object(client, name):
    result = client.api_query(command="show-generic-objects", payload={"name": name})
    Utils.exit_failure("Failed to get object with name " + name, result, client)

    if len(result.data) == 0:
        Utils.print_msg("ERROR: Requested object " + name + " not found")
        client.api_call("discard")
        exit(1)
    elif len(result.data) > 1:
        Utils.print_msg("ERROR: More than one object named " + name + "exists.")
        client.api_call("discard")
        exit(1)
    return result.data[0]


def find_usages(client, original_object):
    where_used = client.api_call("where-used", {"uid": original_object["uid"]})
    in_use = False

    used_in_nat_rules = where_used.data["used-directly"].get("nat-rules")
    if used_in_nat_rules:
        original_object["nat-rule"] = used_in_nat_rules
        in_use = True

    used_in_access_rules = where_used.data["used-directly"].get("access-control-rules")
    if used_in_access_rules:
        original_object["access-rule"] = used_in_access_rules
        in_use = True

    used_in_threat_rules = where_used.data["used-directly"].get("threat-prevention-rules")
    if used_in_threat_rules:
        original_object["threat-rule"] = used_in_threat_rules
        in_use = True

    used_in_object = where_used.data["used-directly"].get("objects")
    if used_in_object:
        original_object["objects"] = used_in_object
        in_use = True

    return in_use


def replace_in_object(client, original_object, new_object):
    for usage in original_object["objects"]:
        if usage["rule"]["type"] != "group" and usage["rule"]["type"] != "service-group":
            Utils.print_msg("WARNING: " + usage["rule"]["type"] + " not supported")
            continue
        payload = {"uid": usage["uid"], "members": {"remove": original_object["uid"]}}
        res = client.api_call("set-" + usage["type"], payload)
        if res.success:
            Utils.print_msg("set-" + usage["type"] + " " + str(payload) + " finished successfully.")
        else:
            if "cannot be locked because it belongs to domain" in res.error_message:
                Utils.print_msg("WARNING: \'" + original_object.get("name") + "\' used in other domain." +
                                " Usage details: \n" + json.dumps(usage))
                continue
            Utils.exit_failure("set-" + usage["type"] + " " + str(payload) + " failed.", res)

        payload = {"uid": usage["uid"], "members": {"add": new_object["uid"]}}
        res = client.api_call("set-" + usage["type"], payload)
        if res.success:
            Utils.print_msg("set-" + usage["type"] + " " + str(payload) + " finished successfully.")
        else:
            Utils.exit_failure("set-" + usage["type"] + " " + str(payload) + " failed.", res, client)


def replace_in_access_rule(client, original_object, new_object):
    for usage in original_object["access-rule"]:
        if usage["rule"]["type"] != "access-rule":
            Utils.print_msg("WARNING: " + usage["rule"]["type"] + " not supported")
            continue
        payload = {"uid": usage["rule"]["uid"], "layer": usage["layer"]["uid"]}
        for col in usage["rule-columns"]:
            payload[col] = {"remove": original_object["uid"]}
        res = client.api_call("set-access-rule", payload)
        if res.success:
            Utils.print_msg("set-access-rule " + str(payload) + " finished successfully.")
        else:
            if "cannot be locked because it belongs to domain" in res.error_message:
                Utils.print_msg("WARNING: \'" + original_object.get("name") + "\' used in other domain." +
                                " Usage details: \n" + json.dumps(usage))
                continue
            Utils.exit_failure("set-access-rule " + str(payload) + " failed.", res, client)

        payload = {"uid": usage["rule"]["uid"], "layer": usage["layer"]["uid"]}
        for col in usage["rule-columns"]:
            payload[col] = {"add": new_object["uid"]}
        res = client.api_call("set-access-rule", payload)
        if res.success:
            Utils.print_msg("set-access-rule " + str(payload) + " finished successfully.")
        else:
            Utils.exit_failure("set-access-rule " + str(payload) + " failed.", res, client)
    pass


def replace_in_nat_rule(client, original_object, new_object):
    for usage in original_object["nat-rule"]:
        if usage["rule"]["type"] != "nat-rule":
            Utils.print_msg("WARNING: " + usage["rule"]["type"] + " not supported")
            continue

        payload = {"uid": usage["rule"]["uid"], "package": usage["package"]["uid"]}
        for col in usage["rule-columns"]:
            payload[col] = new_object["uid"]

        res = client.api_call("set-nat-rule", payload)
        if res.success:
            Utils.print_msg("set-nat-rule " + str(payload) + " finished successfully.")
        else:
            if "cannot be locked because it belongs to domain" in res.error_message:
                Utils.print_msg("WARNING: \'" + original_object.get("name") + "\' used in other domain." +
                                " Usage details: \n" + json.dumps(usage))
                continue
            Utils.exit_failure("set-nat-rule " + str(payload) + " failed.", res, client)


def replace_in_threat_rule(client, original_object, new_object):
    for usage in original_object["threat-rule"]:
        if usage["rule"]["type"] != "threat-rule":
            Utils.print_msg("WARNING: " + usage["rule"]["type"] + " not supported")
            continue

        payload = {"uid": usage["rule"]["uid"], "layer": usage["layer"]["uid"]}
        for col in usage["rule-columns"]:
            if col == "scope":
                payload["protected-scope"] = {"remove": original_object["uid"]}
            else:
                payload[col] = {"remove": original_object["uid"]}
        res = client.api_call("set-threat-rule", payload)
        if res.success:
            Utils.print_msg("set-threat-rule" + str(payload) + " finished successfully.")
        else:
            if "cannot be locked because it belongs to domain" in res.error_message:
                Utils.print_msg("WARNING: \'" + original_object.get("name") + "\' used in other domain." +
                                " Usage details: \n" + json.dumps(usage))
                continue
            Utils.exit_failure("set-threat-rule" + str(payload) + " failed.", res, client)

        payload = {"uid": usage["rule"]["uid"], "layer": usage["layer"]["uid"]}
        for col in usage["rule-columns"]:
            if col == "scope":
                payload["protected-scope"] = {"add": new_object["uid"]}
            else:
                payload[col] = {"add": new_object["uid"]}
        res = client.api_call("set-threat-rule", payload)
        if res.success:
            Utils.print_msg("set-threat-rule" + str(payload) + " finished successfully.")
        else:
            Utils.exit_failure("set-threat-rule" + str(payload) + " failed.", res, client)
    pass


def replace_original_with_new_reference(client, original_object, new_object):
    if original_object.get("nat-rule"):
        replace_in_nat_rule(client, original_object, new_object)
    if original_object.get("access-rule"):
        replace_in_access_rule(client, original_object, new_object)
    if original_object.get("threat-rule"):
        replace_in_threat_rule(client, original_object, new_object)
    if original_object.get("objects"):
        replace_in_object(client, original_object, new_object)
    pass


def get_original_object(client, name, object_type):
    res = client.api_call("show-" + object_type, {"name": name})
    if res.success:
        return res.data
    return


def main():
    user_args = populate_parser()

    Utils.log_file = open(os.path.dirname(os.path.abspath(__file__)) + os.sep + 'replace_references_' +
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
        original_object = get_object(client, user_args.original_reference)
        new_object = get_object(client, user_args.new_reference)

        if not find_usages(client, original_object):
            Utils.print_msg("WARNING: " + original_object.get("name") + " not in use")

        replace_original_with_new_reference(client, original_object, new_object)

        res = client.api_call("publish")
        Utils.exit_failure("Publish operation failed ", res, client)
        Utils.log_file.close()


if __name__ == "__main__":
    main()
