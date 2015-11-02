import os
import unittest
import fake_filesystem_unittest
from tmlib.cfg import WorkflowStepDescription
from tmlib.cfg import WorkflowStageDescription
from tmlib.cfg import WorkflowDescription
from tmlib.cfg import UserConfiguration
from tmlib.args import GeneralArgs
from tmlib.errors import WorkflowDescriptionError


class TestWorkflowStepDescription(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_initialize_with_correct_description_1(self):
        description = {
            'name': 'metaconfig',
            'args': dict()
        }
        step = WorkflowStepDescription(**description)
        self.assertEqual(step.name, description['name'])
        self.assertEqual(dict(step.args), description['args'])
        self.assertIsInstance(step.args, GeneralArgs)

    def test_initialize_with_correct_description_2(self):
        description = {
            'name': 'metaconfig',
            'args': None
        }
        step = WorkflowStepDescription(**description)
        self.assertEqual(step.name, description['name'])
        self.assertNotEqual(dict(step.args), description['args'])
        self.assertIsInstance(step.args, GeneralArgs)

    def test_initialize_with_correct_description_3(self):
        description = {
            'name': 'metaconfig',
            'args': {
                'file_format': 'cellvoyager'
            }
        }
        step = WorkflowStepDescription(**description)
        self.assertEqual(step.name, description['name'])
        self.assertNotEqual(dict(step.args), description['args'])
        self.assertIsInstance(step.args, GeneralArgs)

    def test_initialize_with_incorrect_name(self):
        wrong_description = {
            'name': 'bla',
            'args': None
        }
        with self.assertRaises(WorkflowDescriptionError):
            WorkflowStepDescription(**wrong_description)

    def test_initialize_with_incorrect_args_type_1(self):
        wrong_description = {
            'name': 1,
            'args': dict()
        }
        with self.assertRaises(TypeError):
            WorkflowStepDescription(**wrong_description)

    def test_initialize_with_incorrect_args_type_2(self):
        wrong_description = {
            'name': 'metaconfig',
            'args': [1, 2]
        }
        with self.assertRaises(TypeError):
            WorkflowStepDescription(**wrong_description)

    def test_initialize_with_incorrect_args_type_3(self):
        wrong_description = {
            'name': 'metaconfig',
            'args': {1: 'blabla'}
        }
        with self.assertRaises(TypeError):
            WorkflowStepDescription(**wrong_description)

    def test_initialize_with_incorrect_args_name(self):
        wrong_description = {
            'name': 'metaconfig',
            'args': {'bla': None}
        }
        with self.assertRaises(WorkflowDescriptionError):
            WorkflowStepDescription(**wrong_description)

    def test_return_description(self):
        description = {
            'name': 'metaconfig',
            'args': dict()
        }
        step = WorkflowStepDescription(**description)
        self.assertEqual(dict(step), description)


class TestWorkflowStageDescription(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_initialize_with_correct_description(self):
        description = {
            'name': 'image_conversion',
            'steps': [
                {
                    'name': 'metaextract',
                    'args': dict()
                },
                {
                    'name': 'metaconfig',
                    'args': dict()
                },
            ]
        }
        stage = WorkflowStageDescription(**description)
        self.assertEqual(stage.name, description['name'])
        self.assertEqual(stage.steps[0].name, description['steps'][0]['name'])
        self.assertEqual(dict(stage.steps[0].args),
                         description['steps'][0]['args'])
        self.assertTrue(all(
            [isinstance(s, WorkflowStepDescription) for s in stage.steps]
        ))

    def test_initialize_with_incorrect_steps_value(self):
        wrong_description = {
            'name': 'image_conversion',
            'steps': list()
        }
        with self.assertRaises(ValueError):
            WorkflowStageDescription(**wrong_description)

    def test_initialize_with_incorrect_steps_type(self):
        wrong_description = {
            'name': 'image_conversion',
            'steps': [list()]
        }
        with self.assertRaises(TypeError):
            WorkflowStageDescription(**wrong_description)

    def test_initialize_with_incorrect_name(self):
        wrong_description = {
            'name': 'bla',
            'steps': [
                {
                    'name': 'metaextract',
                    'args': dict()
                }
            ]
        }
        with self.assertRaises(WorkflowDescriptionError):
            WorkflowStageDescription(**wrong_description)

    def test_initialize_with_incorrect_order(self):
        wrong_description = {
            'name': 'image_conversion',
            'steps': [
                {
                    'name': 'metaconfig',
                    'args': dict()
                },
                {
                    'name': 'metaextract',
                    'args': dict()
                }
            ]
        }
        with self.assertRaises(WorkflowDescriptionError):
            WorkflowStageDescription(**wrong_description)

    def test_return_description(self):
        description = {
            'name': 'image_conversion',
            'steps': [
                {
                    'name': 'metaextract',
                    'args': dict()
                }
            ]
        }
        stage = WorkflowStageDescription(**description)
        self.assertEqual(dict(stage), description)


class TestWorkflowDescription(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_initialize_with_correct_description(self):
        description = {
            'stages': [
                {
                    'name': 'image_conversion',
                    'steps': [
                        {
                            'name': 'metaextract',
                            'args': dict()
                        }
                    ]
                }
            ]
        }
        workflow = WorkflowDescription(**description)
        self.assertEqual(workflow.stages[0].name,
                         description['stages'][0]['name'])
        self.assertEqual(workflow.stages[0].steps[0].name,
                         description['stages'][0]['steps'][0]['name'])
        self.assertEqual(dict(workflow.stages[0].steps[0].args),
                         description['stages'][0]['steps'][0]['args'])
        self.assertTrue(all(
            [isinstance(s, WorkflowStageDescription) for s in workflow.stages]
        ))

    def test_initialization_with_incorrect_name(self):
        wrong_description = {
            'bla': [
                {
                    'name': 'image_conversion',
                    'steps': [
                        {
                            'name': 'metaextract',
                            'args': dict()
                        }
                    ]
                }
            ]
        }
        with self.assertRaises(KeyError):
            WorkflowDescription(**wrong_description)

    def test_initialization_with_incorrect_type_1(self):
        wrong_description = {
            'stages':
                {
                    'name': 'image_conversion',
                    'steps': [
                        {
                            'name': 'metaextract',
                            'args': dict()
                        }
                    ]
                }
        }
        with self.assertRaises(TypeError):
            WorkflowDescription(**wrong_description)

    def test_initialization_with_incorrect_type_2(self):
        wrong_description = {
            'stages': [
                {
                    'name': 'image_conversion',
                    'steps': [
                        {
                            'name': 'metaextract',
                            'args': dict()
                        }
                    ]
                }
            ],
            'bla': None
        }
        with self.assertRaises(ValueError):
            WorkflowDescription(**wrong_description)

    def test_initialization_with_incorrect_order(self):
        wrong_description = {
            'stages': [
                {
                    'name': 'image_preprocessing',
                    'steps': [
                        {
                            'name': 'corilla',
                            'args': dict()
                        }
                    ]
                },
                {
                    'name': 'image_conversion',
                    'steps': [
                        {
                            'name': 'metaextract',
                            'args': dict()
                        }
                    ]
                }
            ]
        }
        with self.assertRaises(WorkflowDescriptionError):
            WorkflowDescription(**wrong_description)

    def test_return_description(self):
        description = {
            'stages': [
                {
                    'name': 'image_conversion',
                    'steps': [
                        {
                            'name': 'metaextract',
                            'args': dict()
                        }
                    ]
                }
            ]
        }
        workflow = WorkflowDescription(**description)
        self.assertIsInstance(dict(workflow), dict)


class TestUserConfiguration(fake_filesystem_unittest.TestCase):

    def setUp(self):
        self.setUpPyfakefs()
        self.data_location = '/testdir'
        os.mkdir(self.data_location)
        experiment_name = '150820-Testset-CV'
        self.experiment_dir = os.path.join(self.data_location, experiment_name)
        os.mkdir(self.experiment_dir)  # on the fake filesystem
        self.plate_format = 384

    def tearDown(self):
        self.tearDownPyfakefs()

    def test_initialize_without_setting_directories(self):
        config_settings = {
            'sources_dir': None,
            'plates_dir': None,
            'layers_dir': None,
            'plate_format': self.plate_format
        }
        config = UserConfiguration(
            experiment_dir=self.experiment_dir,
            cfg_settings=config_settings
        )
        self.assertEqual(config.plate_format, self.plate_format)
        expected_sources_dir = os.path.join(self.experiment_dir, 'sources')
        self.assertEqual(config.sources_dir, expected_sources_dir)
        expected_plates_dir = os.path.join(self.experiment_dir, 'plates')
        self.assertEqual(config.plates_dir, expected_plates_dir)
        expected_layers_dir = os.path.join(self.experiment_dir, 'layers')
        self.assertEqual(config.layers_dir, expected_layers_dir)

    def test_initialize_with_setting_directories(self):
        expected_sources_dir = os.path.join(self.data_location, 'sources')
        expected_plates_dir = os.path.join(self.data_location, 'plates')
        expected_layers_dir = os.path.join(self.data_location, 'layers')
        config_settings = {
                'sources_dir': expected_sources_dir,
                'plates_dir': expected_plates_dir,
                'layers_dir': expected_layers_dir,
                'plate_format': self.plate_format
            }
        config = UserConfiguration(
            experiment_dir=self.experiment_dir,
            cfg_settings=config_settings
        )
        self.assertEqual(config.plate_format, self.plate_format)
        self.assertEqual(config.sources_dir, expected_sources_dir)
        self.assertEqual(config.plates_dir, expected_plates_dir)
        self.assertEqual(config.layers_dir, expected_layers_dir)

    def test_to_dict(self):
        expected_sources_dir = os.path.join(self.data_location, 'sources')
        expected_plates_dir = os.path.join(self.data_location, 'plates')
        expected_layers_dir = os.path.join(self.data_location, 'layers')
        config_settings = {
            'sources_dir': expected_sources_dir,
            'plates_dir': expected_plates_dir,
            'layers_dir': expected_layers_dir,
            'plate_format': self.plate_format,
            'workflow': {
                'stages': [
                    {
                        'name': 'image_conversion',
                        'steps': [
                            {
                                'name': 'metaextract',
                                'args': dict()
                            }
                        ]
                    }
                ]
            }
        }
        config = UserConfiguration(
            experiment_dir=self.experiment_dir,
            cfg_settings=config_settings
        )
        self.assertIsInstance(dict(config), dict)

    def test_dump_to_file(self):
        expected_sources_dir = os.path.join(self.data_location, 'sources')
        expected_plates_dir = os.path.join(self.data_location, 'plates')
        expected_layers_dir = os.path.join(self.data_location, 'layers')
        config_settings = {
            'sources_dir': expected_sources_dir,
            'plates_dir': expected_plates_dir,
            'layers_dir': expected_layers_dir,
            'plate_format': self.plate_format,
            'workflow': {
                'stages': [
                    {
                        'name': 'image_conversion',
                        'steps': [
                            {
                                'name': 'metaextract',
                                'args': dict()
                            }
                        ]
                    }
                ]
            }
        }
        config = UserConfiguration(
            experiment_dir=self.experiment_dir,
            cfg_settings=config_settings
        )
        self.assertFalse(os.path.exists(config.cfg_file))
        config.dump_to_file()
        self.assertTrue(os.path.exists(config.cfg_file))