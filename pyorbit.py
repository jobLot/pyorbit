"""
   Copyright 2017 The Foundry Visionmongers Ltd

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import requests
import json
import logging

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class OrbitSyncSource(object):
    """ A component of the OrbitSyncPayload """
    def __init__(self, filepath="", transaction_id="", hash="", last_modified="", metadata={}):
        # filename with path
        self.filepath = filepath
        # client supplied uuid, used to track later
        self.transaction_id = transaction_id
        # client supplied if available (not for 1st download attempt)
        self.hash = hash
        # optional value, if not supplied, the file will have its last modified time set to the time of upload
        self.last_modified = last_modified
        self.metadata = metadata

    def reprJSON(self):
        return dict(filepath=self.filepath, transaction_id=self.transaction_id, hash=self.hash, last_modified=self.last_modified, metadata=self.metadata) 


class OrbitSyncTarget(object):
    """ A component of the OrbitSyncPayload """
    def __init__(self, path):
        self.path = path  

    def reprJSON(self):
#        return dict(target=dict(path=self.path))
        return dict(path=self.path)


class OrbitSyncDirection(object):
    """ A component of the OrbitSyncPayload """
    UP = "up"
    DOWN = "down"


class OrbitSyncPayload(object):
    """ The model used to contain all sync information """
    def __init__(self, direction, sources, target):
        # UP/DOWN
        self.direction = direction
        # List of OrbitSyncSources
        self.sources = sources
        self.target = target

    def reprJSON(self):
        return dict(direction=self.direction, sources=self.sources, target=self.target) 


class PayloadEncoder(json.JSONEncoder):
    """ A custom encoder fore OrbitSyncPayload """
    def default(self, obj):
        if hasattr(obj,'reprJSON'):
            return obj.reprJSON()
        else:
            return json.JSONEncoder.default(self, obj)


class OrbitAPI(object):
    """ 
    A Client of the Orbit API 
    """
    URL = "http://127.0.0.1:5678/api"

    ## Asset Routes
    def get_asset_image_logo(self):
        """ Retrieves Orbits logo from local server. Can be used to detect Orbit's existence """
        req = requests.get("{}/logo".format(OrbitAPI.URL))
        if req.status_code == 200:
            return req.status_code, req.json()
        else: 
            return req.status_code, None  

    ## Group Routes
    def orgs_get(self):
        """ Get all Orgs for logged in user """
        try:
            req = requests.get("{}/orgs".format(OrbitAPI.URL))
        except requests.exceptions.ConnectionError as e:
            logging.warning(e)
            return 503, None


        if req.status_code == 200:
            return req.status_code, req.json()
        else: 
            return req.status_code, None       

    def groups_children_get(self, group_id):
        """ Get children of the supplied group """
        try:
            req = requests.get("{}/groups/{}/children".format(OrbitAPI.URL, group_id))
        except requests.exceptions.ConnectionError as e:
            logging.warning(e)
            return 503, None
        if req.status_code == 200:
            return req.status_code, req.json()
        else: 
            return req.status_code, None

    ## Mount Routes
    def mounts_get(self, group_id):
        """ Get mounts for Group """
        headers = {"active-group" : group_id}
        try:
            req = requests.get("{}/mounts".format(OrbitAPI.URL), headers=headers)
        except requests.exceptions.ConnectionError as e:
            logging.warning(e)
            return 503, None
        if req.status_code == 200:
            return req.status_code, req.json()
        else: 
            return req.status_code, None

    def mounts_files_get(self, group_id, mount_id, path=None):
        """ List the files in the path of the mount supplied """
        headers = {"active-group" : group_id}
        url = "{}/mounts/{}/files".format(OrbitAPI.URL, mount_id)
        if path:
            url += "?path={}".format(path)
        try:
            req = requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError as e:
            logging.warning(e)
            return 503, None
        if req.status_code == 200:
            return req.status_code, req.json()
        else: 
            return req.status_code, None
    
    ## Sync Routes
    def mounts_sync_post(self, group_id, mount_id, payload):
        """ Request the sync process is executed, as described in the payload """
        headers = {"active-group" : group_id}
        json_payload = json.dumps(payload, cls=PayloadEncoder)
        logging.debug(json_payload)
        try:
            req = requests.post("{}/mounts/{}/sync".format(OrbitAPI.URL, mount_id), headers=headers, data=json_payload)
        except requests.exceptions.ConnectionError as e:
            logging.warning(e)
            return 503, None
        if len(req.text):
            logging.debug(req.text)
        # No json object is returned in the body in this case
        return req.status_code, None

    def mounts_sync_get(self, group_id, mount_id, transaction_id=None):
        """ List all known transactions for this mount, or just one if a transaction_id is supplied """
        headers = {"active-group" : group_id}
        url = "{}/mounts/{}/sync".format(OrbitAPI.URL, mount_id)
        if transaction_id:
            url += "/{}".format(transaction_id)
        
        try:
            req = requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError as e:
            logging.warning(e)
            return 503, None

        if req.status_code == 200:
            return req.status_code, req.json()
        else: 
            return req.status_code, None
    
    

