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

