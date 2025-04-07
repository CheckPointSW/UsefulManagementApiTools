# connect_all_domains

The following script connects all domains of a tenant's MDS to the cloud-services portal.

## Instructions
Clone the repository with this command:
```git
git clone https://github.com/CheckPointSW/UsefulManagementApiTools
```
or by clicking the Download ZIP button. 

Download and install the [Check Point API Python SDK](https://github.com/CheckPointSW/cp_mgmt_api_python_sdk) 
repository, follow the instructions in the SDK repository.

To create the required keys, you must go to [Check Point Infinity Portal](https://portal.checkpoint.com) -> Settings -> API Keys -> New -> New Account API Key.
Then choose "Security Management" as the service.

## Usage Syntax

• --client_id: Required. The Client ID.

• --access_key: Required. The Access Key.

• --region: Required. The region. Choices are [ap, us, eu, uae, in].

• --server: The server IP address or hostname, required when running from remote.

• --api_key: The API Key, required when running from remote.

• --api_port: The API Port, required if running from remote, and it isn't the default value (443).

• --debug_file: API calls debug file name.

##Examples

• Running the script on the Multi-Domain Server:
`python connect_all_domains.py --client_id <tenant_client_id> --access_key <tenant_access_key> --region eu --debug_file api_calls.json`

• Running the script from remote:
`python connect_all_domains.py --client_id <tenant_client_id> --access_key <tenant_access_key> --region eu --server 192.168.1.1 --api_key <your_api_key> --api_port 8080`

## Development Environment

The tool is developed using Python language version 3.7 and [Check Point API Python SDK.](https://github.com/CheckPoint-APIs-Team/cpapi-python-sdk)

##Note

In order to run the script, explicit consent must be given.
The connect_all_domains.log and api debug files will be created in project location.