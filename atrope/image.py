# -*- coding: utf-8 -*-

# Copyright 2014 Alvaro Lopez Garcia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import abc
import os.path

from oslo_log import log
import requests
import six

from atrope import exception
from atrope import utils

LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class BaseImage(object):
    @abc.abstractmethod
    def __init__(self, image_info):
        self.uri = None
        self.sha512 = None
        self.identifier = None
        self.location = None
        self.verified = False

    @abc.abstractmethod
    def download(self, dest):
        """Download the image.

        :param dest: destionation directory.
        """

    def verify_checksum(self, location=None):
        """Verify the image's checksum."""

        location = location or self.location
        if location is None:
            raise exception.ImageNotFoundOnDisk(location=location)

        sha512 = utils.get_file_checksum(location)
        if sha512.hexdigest() != self.sha512:
            raise exception.ImageVerificationFailed(
                id=self.identifier,
                expected=self.sha512,
                obtained=sha512.hexdigest()
            )
        self.verified = True


class HepixImage(BaseImage):
    field_map = {
        "ad:group": "group",
        "ad:mpuri": "mpuri",
        "ad:user:fullname": "user_fullname",
        "ad:user:guid": "user_guid",
        "ad:user:uri": "user_uri",
        "dc:description": "description",
        "dc:identifier": "identifier",
        "dc:title": "title",
        "hv:hypervisor": "hypervisor",
        "hv:format": "format",
        "hv:size": "size",
        "hv:uri": "uri",
        "hv:version": "version",
        "sl:arch": "arch",
        "sl:checksum:sha512": "sha512",
        "sl:comments": "comments",
        "sl:os": "os",
        "sl:osname": "osname",
        "sl:osversion": "osversion",
    }
    required_fields = field_map.keys()

    def __init__(self, image_info):
        super(HepixImage, self).__init__(image_info)

        image_dict = image_info.get("hv:image", {})

        for i in self.required_fields:
            value = image_dict.get(i, None)
            if value is None:
                reason = "Invalid image definition, missing '%s'" % i
                raise exception.InvalidImageList(reason=reason)

            attr = self.field_map.get(i)
            setattr(self, attr, value)

    def _download(self, location):
        LOG.info("Downloading image '%s' from '%s' into '%s'",
                 self.identifier, self.uri, location)
        with open(location, 'wb') as f:
            try:
                response = requests.get(self.uri, stream=True)
            except Exception as e:
                LOG.error(e)
                raise exception.ImageDownloadFailed(code=e.errno,
                                                    reason=e.message)

            if not response.ok:
                LOG.error("Cannot download image: (%s) %s",
                          response.status_code, response.reason)
                raise exception.ImageDownloadFailed(code=response.status_code,
                                                    reason=response.reason)

            for block in response.iter_content(1024):
                if block:
                    f.write(block)
                    f.flush()
        try:
            self.verify_checksum(location=location)
        except exception.ImageVerificationFailed as e:
            LOG.error(e)
            raise
        else:
            LOG.info("Image '%s' stored as '%s'",
                     self.identifier, location)

    def download(self, basedir):
        # The image has been already downloaded in this execution.
        if self.location is not None:
            raise exception.ImageAlreadyDownloaded(location=self.location)

        location = os.path.join(basedir, self.identifier)

        if not os.path.exists(location):
            self._download(location)
        else:
            # Image exists, is it checksum valid?
            try:
                self.verify_checksum(location=location)
            except exception.ImageVerificationFailed:
                LOG.warning("Image '%s' found in '%s' is not valid, "
                            "downloading again",
                            self.identifier, location)
                self._download(location)
            else:
                LOG.info("Image '%s' already downloaded into '%s'",
                         self.identifier, location)

        self.location = location
