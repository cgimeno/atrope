# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

from atrope.dispatcher import base

# FIXME(aloga): this should be configurable
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Dispatcher(base.BaseDispatcher):
    """This dummy dispatcher does nothing."""

    def dispatch(self, image):
        """
        In theory I should do something with the image.

        In practise I do nothing, since I am the NOOP dispatcher.
        """
        logging.debug("Dispatching image (noop) %s" % image)
