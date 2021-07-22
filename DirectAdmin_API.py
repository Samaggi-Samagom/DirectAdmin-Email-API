import requests
from requests.auth import HTTPBasicAuth
import warnings
import urllib.parse


class DirectAdminResponse:

    class Unknown:

        def __init__(self, content: str, is_failure: bool = False):
            self.content = content
            self.failure = is_failure

        def raw(self):
            return self.content

        def decode(self):
            return self.content

        def is_error(self):
            return "error" in self.content

    class Text(Unknown):

        def __init__(self, content: str, is_failure: bool = False):
            super().__init__(content, is_failure)

    class Location(Unknown):

        def __init__(self, content: str, is_failure: bool = False):
            super().__init__(content, is_failure)

    class URLEncodedArray(Unknown):

        def __init__(self, content: str, is_failure: bool = False):
            super().__init__(content, is_failure)

        def decode(self, key: str = "list"):
            split = self.content.split(key + "[]=")
            return [(x if x[-1] != "&" else x[:-1]) for x in split if x != ""]

    class URLEncodedString(Unknown):

        def __init__(self, content: str, is_failure: bool = False):
            super().__init__(content, is_failure)

        def decode(self, raw: bool = False):
            res = {}
            pairs = self.content.split("&")
            for pair in pairs:
                key, value = pair.split("=")
                res[urllib.parse.unquote(key)] = urllib.parse.unquote(value) if raw else urllib.parse.unquote(value).split(",")
            return res

        def is_error(self):
            response = self.decode()
            if "error" not in list(response.keys()):
                warnings.warn("Reply does not indicate success nor failure")
                warnings.warn(str(response))
                return False
            else:
                if response["error"][0] == "0":
                    return False
                else:
                    return True


class DirectAdmin:

    def __init__(self, server: str, username: str, password: str, domain: str):
        self.server = server
        self.__user = username
        self.__password = password
        self.domain = domain
        self.__check_domain()

        self.__users_cache = []
        self.__users_cache_valid = False

    def __check_domain(self):
        response = self.send_request("CMD_API_SHOW_DOMAINS", response_type=DirectAdminResponse.URLEncodedArray, failure_response_type=DirectAdminResponse.Text)
        domains = response.decode()
        if self.domain not in domains:
            raise RuntimeError("The domain provided does not exist or you don't have permission to access it")

    def send_request(self, function: str, payload: dict = None, response_type: DirectAdminResponse.__class__ = None, failure_response_type: DirectAdminResponse.__class__ = None):
        if response_type is None:
            response_type = DirectAdminResponse.URLEncodedString
        if failure_response_type is None:
            response_type = DirectAdminResponse.URLEncodedString
        response = requests.post(("https://" if "https://" not in self.server else "") + self.server + ("/" if self.server[-1] != "/" else "") + function, auth=HTTPBasicAuth(self.__user, self.__password), data=payload)

        if response.status_code != 200:
            warnings.warn("Server responded with a non-200 http code while trying to run function {function} on {server}. Response content : {content}".format(function=function, server=self.server, content=response.content))
            return

        direct_admin_response = response_type(response.text)
        failure_response = failure_response_type(response.text, is_failure=True)

        if failure_response.is_error():
            return failure_response
        return direct_admin_response

    def create_user(self, username: str, password: str, quota: int):
        payload = {"action": "create",
                   "domain": self.domain,
                   "quota": quota,
                   "user": username,
                   "passwd": password}

        response = self.send_request("CMD_API_POP", payload, response_type=DirectAdminResponse.Text, failure_response_type=DirectAdminResponse.URLEncodedString)

        if response.failure:
            warnings.warn("Failed to create user")
            warnings.warn(str(response.decode()))
            return False
        return True

    def delete_user(self, username: str):
        payload = {"action": "delete",
                   "domain": self.domain,
                   "user": username}

        response = self.send_request("CMD_API_POP", payload, response_type=DirectAdminResponse.Text)

        if response.failure:
            warnings.warn("Failed to delete user: {user}".format(user=username))
            warnings.warn(str(response.decode()))
            return False
        return True
    
    def change_quota(self, username: str, quota: int):
        payload = {"action": "modify",
                   "domain": self.domain,
                   "user": username,
                   "quota": quota}
        
        response = self.send_request("CMD_API_POP", payload, response_type=DirectAdminResponse.URLEncodedArray, failure_response_type=DirectAdminResponse.URLEncodedArray)
        
        if response.failure:
            warnings.warn("Failed to change user's quota for user {user}".format(user=username))
            warnings.warn(str(response.decode()))
            return False
        return True

    def list_users(self, cache: bool = False):
        self.__users_cache_valid = False

        payload = {"action": "list",
                   "domain": self.domain}

        response = self.send_request("CMD_API_POP", payload, response_type=DirectAdminResponse.URLEncodedArray)

        if response.failure:
            warnings.warn("Failed to list users")
            print(response.decode())
            return

        if cache:
            self.__users_cache = response.decode()
            self.__users_cache_valid = True

        return response.decode()

    def user_exists(self, username: str):
        existing_users = self.__users_cache
        if not self.__users_cache_valid:
            existing_users = self.list_users(cache=False)

        return username in existing_users

    def list_forwarders(self, raw: bool = False):
        payload = {"action": "list",
                   "domain": self.domain}

        response = self.send_request("CMD_API_EMAIL_FORWARDERS", payload, response_type=DirectAdminResponse.URLEncodedString)

        if response.failure:
            warnings.warn("Failed to list forwarders")
            warnings.warn(str(response.decode()))
            return

        return response.decode(raw=raw)

    def modify_forwarder_raw(self, forwarder: str, value: str):
        payload = {"action": "modify",
                   "domain": self.domain,
                   "user": forwarder,
                   "email": value}

        response = self.send_request("CMD_API_EMAIL_FORWARDERS", payload, response_type=DirectAdminResponse.Text)

        if response.failure:
            warnings.warn("Failed to modify forwarder")
            warnings.warn(str(response.decode()))
            return False
        return True

    def remove_user_forwarder(self, username: str, forwarder: str):
        forwarders: dict = self.list_forwarders()

        if forwarder not in forwarders.keys():
            warnings.warn("Forwarder list does not exist, skipping. Forwarder: " + forwarder)
            return False

        current_forwarder = forwarders[forwarder]

        if username not in current_forwarder:
            warnings.warn("The user requested does not exist in the forwarder list, skipping. Username: {username}, Forwarder: {forwarder}".format(username=username, forwarder=forwarder))

        current_forwarder.remove(username)
        new_forwarder = ",".join([u + "@" + self.domain for u in current_forwarder])

        self.modify_forwarder_raw(forwarder, new_forwarder)

    def add_user_forwarder(self, username: str, forwarder: str):
        forwarders = self.list_forwarders()

        if forwarder not in forwarders.keys():
            warnings.warn("Forwarder list does not exist, skipping. Forwarder: " + forwarder)
            return False

        current_forwarder = forwarders[forwarder]

        if username in current_forwarder:
            warnings.warn("The user you're trying to add already exists in the forwarder list, skipping. Username: {username}, Forwarder: {forwarder}".format(username=username, forwarder=forwarder))
            return False

        current_forwarder.append(username)
        new_forwarder = ",".join([u + "@" + self.domain for u in current_forwarder])

        self.modify_forwarder_raw(forwarder, new_forwarder)

    def set_users_forwarder(self, usernames: list, forwarder: str):
        forwarders = self.list_forwarders()

        if forwarder not in forwarders.keys():
            warnings.warn("Forwarder list does not exist, creating. Forwarder: " + forwarder)
            return self.create_forwarder(forwarder_name=forwarder, usernames=usernames)

        new_forwarder = ",".join([u + "@" + self.domain for u in usernames])

        self.modify_forwarder_raw(forwarder, new_forwarder)

    def create_forwarder(self, forwarder_name: str, username: str = None, usernames: list = None):
        if username is None and usernames is None:
            raise RuntimeError("create_forwarder requires either username: str or usernames: list as a parameter. None given.")
        if username is not None and usernames is not None:
            warnings.warn("create_forwarder given both username: str and usernames: list, will use usernames: list")
        elif username is not None and usernames is None:
            usernames = [username]

        forwarder_value = ",".join([u + "@" + self.domain for u in usernames])

        payload = {"action": "create",
                   "domain": self.domain,
                   "user": forwarder_name,
                   "email": forwarder_value}

        response = self.send_request("CMD_API_EMAIL_FORWARDERS", payload, response_type=DirectAdminResponse.Text, failure_response_type=DirectAdminResponse.URLEncodedString)

        if response.failure:
            warnings.warn("Failed to create forwarder")
            warnings.warn(str(response.decode()))
            return False
        return True
