# Python API for Managing MXRoute Email Accounts through DirectAdmin API

## Requirements

### Python
Tested on Python 3.7. Does not support Python 2 due to the usage of `urllib.parse`.

### Packages
- `requests` (and its dependencies)

### Access
Requires access to the following commands on DirectAccess  
-`CMD_API_SHOW_DOMAINS` (required for all use)  
-`CMD_API_EMAIL_FORWARDERS` (required for creating/modifying email forward list)  
-`CMD_API_POP` (required for creating/modifying/deleting email account)
 

## Initialisation
**my_code.py** (Your main Python file):
```
from DirectAdmin_API import DirectAdmin
from credentials import server, username, password, domain

manager = DirectAdmin(server=server, username=username, password=password, domain=domain)
``` 

**credentials.py** (In the same folder as your Python file)
```
server = something.mxrouting.net:2222       #The same url you use to log in to console
username = admin                            #The username used to sign in
password = myPassword                       #The password used to sign in
domain = mydomain.com                       #The domain that you would like to edit
```

## Documentation


### Custom API Request
`.checkRequest(function: str, payload: dict, response_type: DirectAdminResponse.__class__, failure_response_type: DirectAdminResponse.__class__) -> DirectAdminResponse`


>**function:** function that you would like to call. See the API guide [here](https://www.directadmin.com/api.php)  
>**payload:** dictionary data for the POST request, consult API guide  
>**response_type:** see DirectAdminResponseType section below  
>**failure_response_type:** see DirectAdminResponseType section below

Returns DirectAdmin Response Object.  
Query `.failure` on the return value to check if it is the success response or a failure response  
Call `.decode()` on the return value to get the decoded response  
Call `.raw()` on the return value to get the raw string response

<br/>

### Creating an Email Account
`.create_user(username: str, password: str, quota: int) -> bool`

>**username:** username of the user to be created (do NOT include @domain.com)  
>**password:** password of the user to be created (Must have one number and one upper-cased letter)
>**quota:** email storage quota in MB

Returns boolean.  
**TRUE** if operation was successful  
**FALSE** if operation failed. Will print warning with details

<br/>

### Deleting an Email Account 
`.delete_user(username: str)`

>**username:** username of the user to be deleted

Returns boolean.  
**TRUE** if operation was successful  
**FALSE** if operation failed. Will print warning with details

<br/>

### List Users
`.list_users(cache: bool) -> list`

>**cache:** temporarily keeps the list of users in memory for use in `.user_exists()`. Should be kept False otherwise. Cache is cleared if `.list_users()` is called again with `cache=False`

Returns list of string.  
Contains usernames of all email users (does not include @domain.com)

<br/>

### Check if User Exists

`.user_exists(username: str) -> bool`

>**username:** username of the user to be checked

Returns boolean.  
**TRUE** if username exists 
**FALSE** if username does not exist

<br/>

### List All Forwarding Lists

`.list_forwarders(raw: bool) -> dict`

>**raw:** should the code return the usernames in each forward list raw (as a comma-separated string) or as an array. Defaults to False

Returns dictionary.  
If `raw=True`, the dictionary will be in the following format `{string: string}`. The value of each key will be a comma-separated string containing all usernames that the key  will forward to.  
If `raw=False`, the dictionary will be in the following format `{string: [string]}`. The value of each key will be an array of string containing all usernames that the key will forward to it.

<br/>

### Creating a Forwarding List

`.create_forwarder(forwarder_name: str, username: str, usernames: list) -> bool`

>**forwarder_name:** the forwarder name  
> **AND EITHER**  
> **username:** A string containing the (singular) user that the forwarder should forward to  
> **OR**  
> **usernames:** A list of string containing the users that the forwarder should forward to

Returns boolean.  
**TRUE** if operation was successful  
**FALSE** if operation failed. Will print warning with details

<br/>

### Set Forwarding List (Raw Value)
This is used to completely replace an existing forwarding list. The current value for the forwarding list will be replaced.


`.modify_forwarder_raw(forwarder: str, value: str) -> bool`

>**forwarder:** the forwarder name  
>**value:** comma-separated string of all emails (**including** @domain.com)  
>Emails sent to **forwarder** will be forwarded to the users listed in **value**

Returns boolean.  
**TRUE** if operation was successful  
**FALSE** if operation failed. Will print warning with details

<br/>

### Set Forwarding List
This is used to completely replace an existing forwarding list. The current value for the forwarding list will be replaced.

`.set_users_forwarder(usernames: list, forwarder: str) -> bool`

>**usernames:** a list of string containing the usernames of the users which the email sent to the forwarder should be forwarded to (do not include @domain.com)  
>**forwarder:** the forwarder name

Returns boolean.  
**TRUE** if operation was successful  
**FALSE** if operation failed. Will print warning with details

<br/>

### Add User to Forwarding List

`.add_user_forwarder(username: str, forwarder: str) --> bool`

>**username:** username of the username to be removed from the forwarder list (do not include @domain.com)
>**forwarder:** the forwarder name

Returns boolean.  
**TRUE** if operation was successful  
**FALSE** if operation failed. Will print warning with details

<br/>

### Remove User from Forwarding List

`.remove_user_forwarder(username: str, forwarder: str) -> bool`

>**username:** username of the username to be removed from the forwarder list (not including @domain.com)
>**forwarder:** the forwarder name

Returns boolean.  
**TRUE** if operation was successful  
**FALSE** if operation failed. Will print warning with details


### DirectAdminResponseType 

When making a custom API request, the correct response type must be passed to the function to ensure that the response can be understood correctly. For most API calls, the expected response type is provided in the API guide.

```
DirectAdminResponseType.Unknown             #Assumes string
DirectAdminResponseType.Text                #Treats the response as a string
DirectAdminResponseType.URLEncodedString    #Treats the response as a URL, trys to generate a dictionary (e.g. error=0&name=pakkapol)
DirectAdminResponseType.URLEncodedArray(key)#Treats the response as an array embedded in a url (PHP Style) (e.g. list[]=item1&list[]=item2) custom key can be provided (defaults to "list")
```
