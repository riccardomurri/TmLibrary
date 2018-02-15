# TmLibrary - TissueMAPS library for distibuted image analysis routines.
# Copyright (C) 2016  Markus D. Herrmann, University of Zurich and Robin Hafen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import logging

from tmlib.utils import assert_type
from tmlib.log import map_logging_verbosity
from tmlib.workflow.cli import WorkflowStepCLI
from tmlib.workflow.cli import climethod
from tmlib.workflow.args import Argument

logger = logging.getLogger(__name__)


class PopCon(WorkflowStepCLI):

    @assert_type(api_instance='tmlib.workflow.popcon.api.CrowdingEstimator')
    def __init__(self, api_instance, verbosity):
        '''
        Parameters
        ----------
        api_instance: tmlib.workflow.jterator.api.ImageAnalysisPipelineEngine
            instance of API class to which processing is delegated
        verbosity: int
            logging verbosity
        '''
        super(PopCon, self).__init__(api_instance, verbosity)


