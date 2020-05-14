# Useful Management Api Tools
Check Point Useful Management Api Tools contain scripts and tools that were used as solutions for customers.
You can adjust the code according to your organization’s policy / needs.

  - This tools can be executed on Management Server / Multi-Domain servers of version of R80.10 and up.

## Instructions
Clone the repository with this command:
```git
git clone https://github.com/CheckPointSW/UsefulManagementApiTools
``` 
or by clicking the _‘Download ZIP’_ button. 

Download and install the [Check Point API Python SDK](https://github.com/CheckPointSW/cp_mgmt_api_python_sdk) 
repository, follow the instructions in the SDK repository.

## AddTagToObjects.py  
Tool to add a tag to multiple objects. 
<br>The tool supports three modes of tagging by given partial-name: 
*   Add tag to all objects.
*   Add tag to the unused objects.
*   Add tag to the used objects.

<br>If partial name is not supplied the tool will tag all unused objects.

#### Main Options
*__More options and details can be found with the '-h' option by running:__ python AddTagToObjects.py –h*

*   [--tag, -t]&emsp;   The tag name that will be added to the objects.
*   [--partial-name , -pn]&emsp; Add tag to objects shown in object explorer by the provided partial-name. 
This field required in case of using \'--mode\' flag. The default is to add tag to all unused objects in the domain.
*   [--mode, -md]&emsp;  Whether to consider if the objects are used or unused when adding the tag by name.  
<br>&emsp;&emsp;There are three modes, the default is \'unused\':<br> 
    *  unused: add tag only to unused objects with the given partial-name.  
    *  used: add tag only to used objects with the given partial-name.
    *  all: add tag to all objects with the given partial-name.

#### Examples
*   Running the tool on a remote management server: 
<br>```python AddTagToObjects.py --tag TagForUnusedObjects -m 172.23.78.160 -u James -p MySecretPassword!```
<br>The tool runs on a remote management server with IP address 172.23.78.160 and the tag "MyTag" will be added to all unused objects.

*   Running the tool on a Multi-Domain Server for a specific domain: 
<br>```python AddTagToObjects.py -t MyTag -d local_domain -u James -p MySecretPassword!```

*   Running the tool on a Security Management Server with partial name: 
<br>```python AddTagToObjects.py --tag my_host --partial-name "host_" -u James -p MySecretPassword!```
<br>The tool will add "my_host" tag to all the unused objects that are found in the explorer with the given partial-name.

*   Running the tool on a Security Management Server with partial name of unused objects:
<br>```python AddTagToObjects.py  --tag my_host --partial-name "host_" --mode all -u James -p MySecretPassword!```
<br>The tool will add "my_host" tag to all the objects that are found in the explorer with the given partial-name.


## ReplaceReference.py  
Replace references of two given objects. 
The tool supports replacement in Access, Threat and Nat rules, and in groups and service-groups. 

#### Main Options
*__More options and details can be found with the '-h' option by running:__ python ReplaceReference.py –h*

*   [--original-reference, -o]&emsp;   The full name of the replaced object, must be unique name.
*   [--new-reference, -n]&emsp; The full name of the new object, must be unique name. 

#### Examples
*   Running the tool on a remote management server: 
<br>```python ReplaceReference.py --original-reference old_host --new-reference new_host -m 172.23.78.160 -u James -p MySecretPassword!```
<br>The tool runs on a remote management server with IP address 172.23.78.160 and replaces references from old_host to new_host.

*   Running the tool on a Multi-Domain Server for a specific domain: 
<br>```python ReplaceReference.py -o Global_object -n local_object -d local_domain -u James -p MySecretPassword!```
<br>The tool can replace references to a Global object with references to a local object.


## Development Environment
The tool is developed using Python language version 2.7, version 3.7 and [Check Point API Python SDK](https://github.com/CheckPointSW/cp_mgmt_api_python_sdk).




