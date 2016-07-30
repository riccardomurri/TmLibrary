import os
import logging
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy import UniqueConstraint

from tmlib.models import ExperimentModel, DateMixIn
from tmlib.models import distribute_by_replication
from tmlib.models.utils import remove_location_upon_delete
from tmlib.utils import autocreate_directory_property

logger = logging.getLogger(__name__)

#: Format string for channel locations
CHANNEL_LOCATION_FORMAT = 'channel_{id}'


@remove_location_upon_delete
@distribute_by_replication
class Channel(ExperimentModel, DateMixIn):

    '''A *channel* represents all *images* across different time points and
    spatial positions that were acquired with the same illumination and
    microscope filter settings.

    Attributes
    ----------
    name: str
        name of the plate
    root_directory: str
        absolute path to root directory where channel is located on disk
    wavelength: str
        name of the corresponding wavelength
    layers: List[tmlib.models.ChannelLayer]
        layers belonging to the channel
    illumstats_files: List[tmlib.model.IllumstatsFile]
        illumination statistics files that belongs to the channel
    '''

    #: str: name of the corresponding database table
    __tablename__ = 'channels'

    __table_args__ = (UniqueConstraint('name'), UniqueConstraint('index'))

    # Table columns
    name = Column(String, index=True)
    index = Column(Integer, index=True)
    wavelength = Column(String, index=True)
    bit_depth = Column(Integer)
    root_directory = Column(String)

    def __init__(self, name, index, wavelength, bit_depth, root_directory):
        '''
        Parameters
        ----------
        name: str
            name of the channel
        index: int
            zero-based channel index
        wavelength: str
            name of the corresponding wavelength
        bit_depth: int
            number of bits used to indicate intensity of pixels
        root_directory: str
            absolute path to root directory on disk where channel should
            be created in
        '''
        self.name = name
        self.index = index
        self.wavelength = wavelength
        self.bit_depth = bit_depth
        self.root_directory = root_directory

    @autocreate_directory_property
    def location(self):
        '''str: location were the channel is stored'''
        if self.id is None:
            raise AttributeError(
                'Channel "%s" doesn\'t have an entry in the database yet. '
                'Therefore, its location cannot be determined.' % self.name
            )
        return os.path.join(
            self.root_directory, CHANNEL_LOCATION_FORMAT.format(id=self.id)
        )

    @autocreate_directory_property
    def layers_location(self):
        '''str: location where layers are stored'''
        return os.path.join(self.location, 'layers')

    def __repr__(self):
        return '<Channel(id=%r, name=%r)>' % (self.id, self.name)

    def as_dict(self):
        '''
        Return attributes as key-value pairs.

        Returns
        -------
        dict
        '''
        return {
            'id': self.id,
            'name': self.name,
            'layers': [l.as_dict() for l in self.layers]
        }
