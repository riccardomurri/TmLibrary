import os
import logging
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from tmlib.models.base import Model
from tmlib.models.utils import auto_create_directory
from tmlib.models.utils import auto_remove_directory
from ..utils import autocreate_directory_property

logger = logging.getLogger(__name__)

#: Format string for acquisition locations
ACQUISITION_LOCATION_FORMAT = 'acquisition_{id}'


@auto_remove_directory(lambda obj: obj.location)
@auto_create_directory(lambda obj: obj.location)
class Acquisition(Model):

    '''An *acquisition* contains all files belonging to one microscope image
    acquisition process. Note that in contrast to a *cycle*, an *acquisition*
    may contain more than one time point.

    The incentive to grouped files this way relates to the fact that most
    microscopes generate separate metadata files for each *acquisition*.

    Attributes
    ----------
    name: str
        name of the acquisition
    description: str
        description of the acquisition
    status: str
        processing status
    plate_id: int
        ID of the parent plate
    plate: tmlib.models.Plate
        parent plate to which the acquisition belongs
    microscope_image_files: List[tmlib.models.MicroscopeImageFile]
        image files generated by the microscope
    microscope_metadata_files: List[tmlib.models.MicroscopeMetadataFile]
        metadata files generated by the microscope
    ome_xml_files: List[tmlib.models.OmeXmlFile]
        OMEXML files extracted from microscope image files
    '''

    #: Name of the corresponding database table
    __tablename__ = 'acquisitions'

    #: Table columns
    name = Column(String, index=True)
    description = Column(Text)
    status = Column(String)
    plate_id = Column(Integer, ForeignKey('plates.id'))

    #: Relationships to other tables
    plate = relationship('Plate', backref='acquisitions')

    def __init__(self, name, plate, description=''):
        '''
        Parameters
        ----------
        name: str
            name of the acquisition
        plate: tmlib.models.Plate
            parent plate to which the acquisition belongs
        description: str, optional
            description of the acquisition
        '''
        # TODO: ensure that name is unique within plate
        self.name = name
        self.description = description
        self.plate_id = plate.id
        self.status = 'WAITING'

    @property
    def location(self):
        '''str: location were the acquisition content is stored'''
        if self.id is None:
            raise AttributeError(
                'Acquisition "%s" doesn\'t have an entry in the database yet. '
                'Therefore, its location cannot be determined.' % self.name
            )
        return os.path.join(
            self.plate.aqusitions_location,
            ACQUISITION_LOCATION_FORMAT.format(id=self.id)
        )

    @autocreate_directory_property
    def microscope_images_location(self):
        '''str: location where microscope image files are stored'''
        return os.path.join(self.location, 'microscope_images')

    @autocreate_directory_property
    def microscope_metadata_location(self):
        '''str: location where microscope metadata files are stored'''
        return os.path.join(self.location, 'microscope_metadata')

    @autocreate_directory_property
    def omexml_location(self):
        '''str: location where extracted OMEXML files are stored'''
        return os.path.join(self.location, 'omexml')

    def as_dict(self):
        '''Return attributes as key-value pairs.

        Returns
        -------
        dict
        '''
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'image_files': [im.as_dict() for im in self.image_files],
            'metadata_files': [md.as_dict() for md in self.metadata_files]
        }

    def __repr__(self):
        return '<Acquisition(id=%r, name=%r)>' % (self.id, self.name)

    # @property
    # def image_mapping_file(self):
    #     '''
    #     Returns
    #     -------
    #     str
    #         name of the file that contains key-value pairs for mapping
    #         the images stored in the original image files to the
    #         the OME *Image* elements in `image_metadata`
    #     '''
    #     return os.path.join(self.location, 'image_file_mapping.json')

    # @property
    # def image_mapping(self):
    #     '''
    #     Returns
    #     -------
    #     List[tmlib.metadata.ImageFileMapping]
    #         key-value pairs to map the location of individual planes within the
    #         original files to the *Image* elements in the OMEXML
    #     '''
    #     image_mapping = list()
    #     with JsonReader() as reader:
    #         hashmap = reader.read(self.image_mapping_file)
    #     for element in hashmap:
    #         image_mapping.append(ImageFileMapping(**element))
    #     return image_mapping
