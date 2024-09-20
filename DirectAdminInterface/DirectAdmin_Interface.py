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
                # warnings.warn("Reply does not indicate success nor failure")
                # warnings.warn(str(response))
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
            failure_response_type = DirectAdminResponse.URLEncodedString
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

    def get_all_limits(self):
        payload = {"action": "list",
                   "domain": self.domain,
                   "type": "quota"}

        response = self.send_request("CMD_API_POP", payload, response_type=DirectAdminResponse.URLEncodedString)

        if response.failure:
            warnings.warn("Failed to list users")
            print(response.decode())
            return

        result = {}
        response_decoded = response.decode()
        for user in response_decoded.keys():
            data = {}
            pairs = response_decoded[user][0].split("&")
            for pair in pairs:
                key, value = pair.split("=")
                data[urllib.parse.unquote(key)] = urllib.parse.unquote(value)
            result[user] = data

        return result

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
                   "quota": quota,
                   "passwd": '',
                   "passwd2": ''}

        response = self.send_request("CMD_API_POP", payload, response_type=DirectAdminResponse.URLEncodedArray, failure_response_type=DirectAdminResponse.URLEncodedString)

        if response.failure:
            warnings.warn("Failed to change user's quota for user {user}".format(user=username))
            warnings.warn(str(response.decode()))
            return False
        return True

    def change_password(self, username: str, password: str):
        payload = {"action": "modify",
                   "domain": self.domain,
                   "user": username,
                   "passwd": password,
                   "passwd2": password}

        response = self.send_request("CMD_API_POP", payload, response_type=DirectAdminResponse.URLEncodedArray,
                                     failure_response_type=DirectAdminResponse.URLEncodedString)

        if response.failure:
            warnings.warn(f"Failed to change user's password for username: {username}")
            warnings.warn(str(response.decode()))
            return False
        return True

    def list_users(self, cache: bool = False, raw: bool = False):
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

        if raw:
            return response.decode()
        else:
            quo = self.get_all_limits()
            return [DirectAdminEmailUser(self, usr, quo[usr]) if usr in quo.keys() else DirectAdminEmailUser(self, usr) for usr in response.decode()]

    def user_exists(self, username: str):
        existing_users = self.__users_cache
        if not self.__users_cache_valid:
            existing_users = self.list_users(cache=False, raw=True)

        return username in existing_users

    def list_forwarders(self, raw: bool = False):
        payload = {"action": "list",
                   "domain": self.domain}

        response = self.send_request("CMD_API_EMAIL_FORWARDERS", payload, response_type=DirectAdminResponse.URLEncodedString)

        if response.failure:
            warnings.warn("Failed to list forwarders")
            warnings.warn(str(response.decode()))
            return

        if not raw:
            decoded = response.decode(raw=False)
            limits = self.get_all_limits()
            return [DirectAdminEmailForwarder(self, fwd, data=decoded, limits_cache=limits) for fwd in decoded.keys()]
        else:
            return response.decode(raw=False)

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
        forwarders = self.list_forwarders(raw=True)

        if forwarder not in forwarders:
            warnings.warn("Forwarder list does not exist, skipping. Forwarder: " + forwarder)
            return False

        current_forwarder = forwarders[forwarder]

        if username in current_forwarder:
            warnings.warn("The user you're trying to add already exists in the forwarder list, skipping. Username: {username}, Forwarder: {forwarder}".format(username=username, forwarder=forwarder))
            return False

        current_forwarder.append(username)
        new_forwarder = ",".join([u + (("@" + self.domain) if "@" not in u else "") for u in current_forwarder])

        self.modify_forwarder_raw(forwarder, new_forwarder)

    def set_users_forwarder(self, usernames: list, forwarder: str):
        forwarders = self.list_forwarders(raw=True)

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


class DirectAdminEmailUser:

    def __init__(self, domain_object: DirectAdmin, username: str, limits: dict = None):
        self.username = username
        self.domain_object = domain_object
        if limits is None:
            self.__quota = -1
            self.__usage = -1
            return
        self.__quota = int(limits["quota"]) if limits["quota"] is not None else -1
        self.__usage = int(limits["usage_bytes"]) if limits["usage_bytes"] is not None else -1

    def quota(self):
        if self.__quota == -1:
            self.get_limits()
        return int(self.__quota)/1024/1024

    def usage(self):
        if self.__usage == -1:
            self.get_limits()
        return int(self.__usage)/1024/1024

    def get_limits(self):
        quotas = self.domain_object.get_all_limits()
        if self.username not in quotas.keys():
            raise RuntimeError("DirectAdminEmailUser.get_quota: user not found.")
        self.__quota = quotas[self.username]["quota"]
        self.__usage = quotas[self.username]["usage_bytes"]

    def add_to(self, forwarder: str):
        return self.domain_object.add_user_forwarder(self.username, forwarder)

    def delete(self):
        return self.domain_object.delete_user(self.username)


class DirectAdminEmailForwarder:

    def __init__(self, domain_object: DirectAdmin, name: str, auto_save=True, auto_update=True, data: dict = None, limits_cache: dict = None):
        self.name = name
        self.members = []
        self.domain_object = domain_object
        self.__auto_save = auto_save
        self.__auto_update = auto_update
        self.__is_init = False

        if data is not None:
            limits_cache = self.domain_object.get_all_limits() if limits_cache is None else limits_cache
            for user in data[self.name]:
                user = user.replace("@" + domain_object.domain, "")
                if user in limits_cache.keys():
                    self.members.append(DirectAdminEmailUser(self.domain_object, user, limits_cache[user]))
            self.__is_init = True

    def get_members(self):
        forwarders = self.domain_object.list_forwarders(raw=True)
        if forwarders is None:
            raise RuntimeError("DirectAdminEmailForwarder.update_members: Unable to get forwarders, cannot continue")

        if self.name not in forwarders.keys():
            warnings.warn("DirectAdminEmailForwarder.update_members: forwarder does not currently exist. Value initialised as []")
            self.members = []
            self.__is_init = True
            return

        quo = self.domain_object.get_all_limits()
        for user in forwarders[self.name]:
            username = user.replace("@" + self.domain_object.domain, "")
            self.members.append(DirectAdminEmailUser(self.domain_object, username, quo[username] if username in quo.keys() else None))
        self.__is_init = True

    def __init_check(self):
        if not self.__is_init:
            raise RuntimeError("DirectAdminEmailForwarder.get_members must be called at least once before using it")

    def save(self):
        self.__init_check()
        return self.domain_object.set_users_forwarder(usernames=[usr.username for usr in self.members], forwarder=self.name)

    def add_member(self, username: str):
        self.__init_check()
        if self.__auto_update:
            self.get_members()

        self.members.append(DirectAdminEmailUser(self.domain_object, username))

        if self.__auto_save:
            return self.save()

    def remove_member(self, username: str):
        self.__init_check()
        if self.__auto_update:
            self.get_members()

        if username not in self.members:
            warnings.warn("DirectAdminEmailForwarder.remove_member: user requested to be removed does not exist in the forwarding list")
            return
        self.members.remove(DirectAdminEmailUser(self.domain_object, username))

        if self.__auto_save:
            return self.save()

    def members_usernames(self):
        return [member.username for member in self.members]

    def average_quota(self):
        if len(self.members) == 0:
            return 0
        return sum([usr.quota() for usr in self.members])/len(self.members)

    def average_usage(self):
        if len(self.members) == 0:
            return 0
        return sum([usr.usage() for usr in self.members]) / len(self.members)
