# Python Interface for Managing MXRoute Email Accounts through DirectAdmin API

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
 
## Installation

Run the following command to install as a library.  
```bash
git+git://github.com/Samaggi-Samagom/DirectAdmin-Email-API@master#DirectAdmin_API=DirectAdmin-Email-API
````

## Usage
**my_code.py** (Your main Python file):
```python
from DirectAdminInterface.DirectAdmin_Interface import *
from credentials import server, username, password, domain

manager = DirectAdmin(server=server, username=username, password=password, domain=domain)
``` 

**credentials.py** (In the same folder as your Python file)
```python
server = "something.mxrouting.net:2222"       #The same url you use to log in to console
username = "admin"                            #The username used to sign in
password = "myPassword"                       #The password used to sign in
domain = "mydomain.com"                       #The domain that you would like to edit
```

# Documentation

## DirectAdmin


### Initialisation

`DirectAdmin(server: str, username: str, password: str, domain: str)`

> **server:** the url that you normally use for logging in to the DirectAdmin web console  
> **username:** the username of the (admin) account  
> **password:** the password of the same account  
> **domain:** the domain that you would like to edit (e.g. domain.com)

### Custom API Request
`.checkRequest(function: str, payload: dict, response_type: DirectAdminResponse.__class__, failure_response_type: DirectAdminResponse.__class__) -> DirectAdminResponse`


>**function:** function that you would like to call. See the API guide [here](https://www.directadmin.com/api.php)  
>**payload:** dictionary data for the POST request, consult API guide  
>**response_type:** see DirectAdminResponseType section below  
>**failure_response_type:** see DirectAdminResponseType section below

Returns DirectAdminResponse Object.  
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

### Modifying Account Quota
`.change_quota(username: str, quota: int) -> bool`

>**username:** username of the user whose quota is to be changed (do NOT include @domain.com)
>**quota:** the quota of the user in MB

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
`.list_users(cache: bool, raw: bool) -> list`

>**cache:** temporarily keeps the list of users in memory for use in `.user_exists()`. Should be kept False otherwise. Cache is cleared if `.list_users()` is called again with `cache=False`  
>**raw:** should the function return the list of users as a list of string or as a list of `DirectAdminEmailUser`. Defaults to FALSE.

Returns an array.
If `raw=True`, returns an array of string containing the usernames
If `raw=False`, returns an array of `DirectAdminEmailUser` with embedded quota/limit information

<br/>

### Get the User's Quotas/Limits
`.get_all_limits() -> dict`

Returns dictionary.  
The dictionary will be in the following format {<username>: {"limit": <limit>, "quota": <quota>, "usage": <usage>, "usage_bytes": <usage in bytes>}}

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

Returns dictionary or array.  
If `raw=True`, the dictionary will be in the following format `{string: string}`. The value of each key will be a comma-separated string containing all usernames that the key  will forward to.  
If `raw=False`, an array of `DirectAdminEmailForwarder` will be returned. See below for more detail.

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

>**username:** username of the username to be added to the forwarder list (do not include @domain.com)
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

<br/>

## DirectAdminEmailUser
`DirectAdminEmailUser` is a class returned from `.list_users()` of `DirectAdmin`. It contains values for each user and provides a few functions.

### Initialisation

`DirectAdminEmailUser(domain_object: DirectAdmin, username: str, limits: dict?)`
> **domain_object:** an object of type `DirectAdmin` which this user is a member of  
> **username:** the username of the user  
> **limits (Optional):** the limits for the specific user, must be in the following format `{"limit": <int>, "usage_bytes": <int>, "usage": <int>, "quota": <int>}`. If this is not provided if can be obtained calling `.get_limits()`

<br/>

### Getting the User's Quota
`.quota()`

Returns integer.  
The integer represents the user's quota in Megabytes

<br/>

### Getting the User's Usage

`.usage()`

Returns integer.  
The integer represents the user's usage in Megabytes

<br/>

### Getting User's Usage/Limits

Used to reload the limits for the specific user. This function is called the first time you call `.quota()` or `.usage()`

`.get_limits()`

Does not return a value (None)

<br/>

### Add the user to a forwarding list

`.add_to(forwarder: str) -> bool`

> **forwarder:** the name of the forwarding list which the user should be added to

Returns boolean.  
**TRUE** if operation was successful  
**FALSE** if operation failed. Will print warning with details

<br/>


### Delete the user

`.delete()`

Returns boolean.  
**TRUE** if operation was successful  
**FALSE** if operation failed. Will print warning with details

<br/>

## DirectAdminEmailForwarder

### Initialisation

Used to initialise the object. If the object is initialised with `data=None`, `.get_members()` **must** be called once before using it.

`DirectAdminEmailForwarder(domain_object: DirectAdmin, name: str, auto_save: bool, auto_update: bool, data: dict, limits_cache: dict)`

> **domain_object:** an object of type `DirectAdmin` which this forwarder is a member of  
> **name:** the name of the forwarder  
> **auto_save:** should the changes to this object be automatically be saved onto the server (must call `.save()` otherwise). Defaults to TRUE  
> **auto_update:** should the object be updated to match the data on the server whenever a function of this object is called (must call `.update()` otherwise). Defaults to TRUE  
> **data (Optional) :** the forwarder data obtained from `DirectAdmin.list_forwarders()`. This allows the object to be initialised with its members without calling `.get_members()`   
> **limits_cache (Optional) :** limits data obtained from `DirectAdmin.get_all_limits()`. This allows the members of the forwarders to be initialised with limit/usage data

<br/>

### Getting members

Used to update the list of members in the forwarder. If `data` is not provided when initialising the object, this method must be called once before using the other methods.

`.get_members()`

Does not return (None)

<br/>

### Saving

Used to save the forwarding list to the server if `auto_save` is disabled

`.save() -> bool`

Returns boolean.  
**TRUE** if operation was successful  
**FALSE** if operation failed. Will print warning with details

<br/>

### Add Member to the Forwarding List

`.add_member(username: str) -> bool?`

> **username:** username of the user to be added to the list

Returns boolean IF `auto_save` is TRUE  
**TRUE** if operation was successful  
**FALSE** if operation failed. Will print warning with details

<br/>

### Remove member from the Forwarding List (UNTESTED)

`.remove_member(username: str) -> bool?`

> **username:** username of the user to be removed from the list

Returns boolean IF `auto_save` is TRUE  
**TRUE** if operation was successful  
**FALSE** if operation failed. Will print warning with details

<br/>

### Get Members' Usernames

`.members_usernames() -> list`

Returns an array of string.  
The array contains the usernames of all users in the forwarding list.

<br/>

### Getting the Members' Average Quota

`.average_quota() -> float`

Returns float.  
The value of the float represents the average quota in Megabytes

<br/>

### Getting the Members' Average Usage

`.average_usage() -> float`

Returns float.
The value of the float represents the average usage in Megabytes

<br/>

## DirectAdminResponseType 

When making a custom API request, the correct response type must be passed to the function to ensure that the response can be understood correctly. For most API calls, the expected response type is provided in the API guide.

```
DirectAdminResponseType.Unknown             #Assumes string
DirectAdminResponseType.Text                #Treats the response as a string
DirectAdminResponseType.URLEncodedString    #Treats the response as a URL, trys to generate a dictionary (e.g. error=0&name=pakkapol)
DirectAdminResponseType.URLEncodedArray(key)#Treats the response as an array embedded in a url (PHP Style) (e.g. list[]=item1&list[]=item2) custom key can be provided (defaults to "list")
```
