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

from oslo_config import cfg
from oslo_log import log
import six
import yaml

from atrope import cache
import atrope.dispatcher.manager
from atrope import exception
import atrope.image_list.hepix

CONF = cfg.CONF
CONF.import_opt("hepix_sources", "atrope.image_list.hepix", group="sources")

LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class BaseImageListManager(object):
    def __init__(self, dispatcher=None):
        self.cache_manager = cache.CacheManager()
        self._dispatcher = None

        self.lists = {}
        self._load_sources()

    @property
    def dispatcher(self):
        if self._dispatcher is None:
            self._dispatcher = atrope.dispatcher.manager.DispatcherManager()
        return self._dispatcher

    @abc.abstractmethod
    def _load_sources(self):
        """Load the image sources from disk."""

    @abc.abstractmethod
    def write_image_list_sources(self):
        """Write image sources to disk."""

    def _fetch_and_verify(self, l):
        """Fetch and verify an image list.

        If there are errors loading the list the appropriate attributes won't
        be set, so there is no need to fail here, but rather return the list.
        """
        try:
            l.fetch()
        except exception.AtropeException as e:
            LOG.error("Error loading list '%s' from '%s', reason: %s",
                      l.name, l.url, e.message)
            LOG.debug("Exception while downloading list '%s'",
                      l.name, exc_info=e)
        return l

    def add_image_list_source(self, image_list, force=False):
        """Add an image source to the loaded sources."""
        if image_list.name in self.lists and not force:
            raise exception.DuplicatedImageList(id=image_list.name)

        self.lists[image_list.name] = image_list

    def fetch_list(self, image_list):
        """Fetch (and verify) an individual list."""
        l = self.lists.get(image_list)
        if l is None:
            raise exception.InvalidImageList(reason="not found in config")
        return self._fetch_and_verify(l)

    def fetch_lists(self):
        """Fetch (and verify) all the configured lists."""
        all_lists = []
        for l in self.lists.values():
            l = self._fetch_and_verify(l)
            all_lists.append(l)

        return all_lists

    def sync_cache(self):
        self.fetch_lists()
        self.cache_manager.sync(self.lists)

    def dispatch(self, sync):
        if sync:
            fn = self.dispatcher.dispatch_list_and_sync
        else:
            fn = self.dispatcher.dispatch_list

        for l in self.lists.values():
            fn(l)


class YamlImageListManager(BaseImageListManager):
    def __init__(self):
        super(YamlImageListManager, self).__init__()

    def _load_sources(self):
        """Load sources from YAML file."""

        try:
            with open(CONF.sources.hepix_sources, "rb") as f:
                image_lists = yaml.safe_load(f) or {}
        except IOError as e:
            raise exception.CannotOpenFile(file=CONF.sources.hepix_sources,
                                           errno=e.errno)

        for name, list_meta in image_lists.iteritems():
            l = atrope.image_list.hepix.HepixImageListSource(
                name,
                url=list_meta.pop("url", ""),
                enabled=list_meta.pop("enabled", True),
                subscribed_images=list_meta.pop("images", []),
                prefix=list_meta.pop("prefix", ""),
                **list_meta)
            self.lists[name] = l

    def write_image_list_sources(self):
        """Write images into YAML file."""
        lists = {}
        for name, image_list in self.lists.iteritems():
            lists[name] = {"url": image_list.url,
                           "enabled": image_list.enabled,
                           "endorser": image_list.endorser,
                           "token": image_list.token,
                           "prefix": image_list.prefix,
                           "subscribed images": image_list.subscribed_images}
        dump = yaml.dump(lists)
        if not dump:
            raise exception.AtropeException()

        with open(CONF.sources.hepix_sources, "w") as f:
            f.write(dump)
