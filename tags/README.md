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
