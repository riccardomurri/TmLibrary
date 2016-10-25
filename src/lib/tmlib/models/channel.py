import os
import logging
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy import UniqueConstraint

from tmlib.models.base import ExperimentModel, DateMixIn

logger = logging.getLogger(__name__)

#: Format string for channel locations
CHANNEL_LOCATION_FORMAT = 'channel_{id}'


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
    experiment_id: int
        ID of the parent experiment
    experiment: tmlib.models.Experiment
        parent experiment
    '''

    #: str: name of the corresponding database table
    __tablename__ = 'channels'

    __table_args__ = (UniqueConstraint('name'), UniqueConstraint('index'))

    # Table columns
    name = Column(String, index=True)
    index = Column(Integer, index=True)
    wavelength = Column(String, index=True)
    bit_depth = Column(Integer)
    experiment_id = Column(
        Integer,
        ForeignKey('experiment.id', onupdate='CASCADE', ondelete='CASCADE'),
        index=True
    )

    # Relationships to other tables
    experiment = relationship(
        'Experiment',
        backref=backref('channels', cascade='all, delete-orphan')
    )

    def __init__(self, name, index, wavelength, bit_depth):
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
        '''
        self.name = name
        self.index = index
        self.wavelength = wavelength
        self.bit_depth = bit_depth
        self.experiment_id = 1

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