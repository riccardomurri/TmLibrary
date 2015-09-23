import os
import re
import glob
from copy import copy
import shutil
from .. import utils
from ..errors import PipelineOSError


def list_jtprojects(directory):
    '''
    List Jterator projects in a given directory.
    A Jterator project is defined as a folder containing a `.pipe` file.

    Parameters
    ----------
    directory: str
        absolute path to a directory
    '''
    projects = [name for name in os.listdir(directory)
                if (os.path.isdir(os.path.join(directory, name))
                and glob.glob(os.path.join(directory, name, '*.pipe')))]
    if not projects:
        print 'No Jterator projects found in %s' % directory
    return projects


class JtProject(object):

    '''
    A class for a Jterator project.

    A Jterator project is defined as a folder containing a `.pipe` file.
    The class holds information about the project, in particular on the content
    of YAML pipeline and module descriptor files that can be edited in the
    JtUI app.
    '''
    def __init__(self, project_dir, pipe_name, pipe=None, handles=None):
        '''
        Initialize an instance of class Jtproject.

        Parameters
        ----------
        project_dir: str
            path to the project folder
        pipe_name: str
            name of the pipeline
        pipe: dict
            pipeline description
        handles: List[dict]
            module descriptions
        '''
        self.project_dir = project_dir
        self.pipe_name = pipe_name
        self.pipe = pipe
        self.handles = handles

    @property
    def experiment(self):
        '''
        Returns
        -------
        str
            name of the corresponding experiment
        '''
        self._experiment = os.path.basename(self.project_dir)
        return self._experiment

    @property
    def pipe(self):
        '''
        Returns
        -------
        dict
            name and description of the pipeline
        '''
        return self._pipe

    @pipe.setter
    def pipe(self, value):
        self._pipe = value

    @property
    def handles(self):
        '''
        Returns
        -------
        List[dict]
            name and description of modules
        '''
        return self._handles

    @handles.setter
    def handles(self, value):
        self._handles = value

    def _get_pipe_file(self, directory=None):
        if not directory:
            directory = self.project_dir
        pipe_files = glob.glob(os.path.join(directory, '*.pipe'))
        if len(pipe_files) == 1:
            return pipe_files[0]
        elif len(pipe_files) > 1:
            raise PipelineOSError(
                    'More than more .pipe file found: %s' % directory)
        if not pipe_files:
            raise PipelineOSError(
                    'No .pipe file found: %s' % directory)

    def _get_handles_files(self, directory=None):
        if not directory:
            directory = os.path.join(self.project_dir, 'handles')
        else:
            directory = os.path.join(directory, 'handles')
        handles_files = glob.glob(os.path.join(directory, '*.handles'))
        if not handles_files:
            # We don't raise an exception, because an empty handles folder
            # can occur, for example upon creation of a new project
            print('No .handles files found: %s' % directory)
        return handles_files

    @staticmethod
    def _get_descriptor_name(filename):
        return os.path.splitext(os.path.basename(filename))[0]

    @staticmethod
    def _replace_values(old, new):
        # Recursively replace the values of key-value pairs.
        # The comments below are guides for the .pipe pipeline descriptor file,
        # but it works similarly for .handles files.
        for k1, v1 in old.iteritems():
            # These are the main keys in the pipeline descriptor file:
            # 'project', 'jobs', 'description'
            if isinstance(v1, dict):
                # This affects 'project' and 'jobs'
                for k2, v2 in v1.iteritems():
                    if isinstance(v2, list):
                        # This is the array of 'pattern' in the 'jobs' section
                        old[k1][k2] = []
                        for i, element in enumerate(new[k1][k2]):
                            if isinstance(element, dict):
                                for k3 in copy(element):
                                    # Remove 'hashKey' elements
                                    # (included by Javascript)
                                    if re.search(r'\$\$hashKey', k3):
                                        new[k1][k2][i].pop(k3, None)
                                old[k1][k2].append(new[k1][k2][i])

                    else:
                        old[k1][k2] = new[k1][k2]
            elif isinstance(v1, list):
                # This affects 'description' (the array of modules)
                old[k1] = []
                for i, element in enumerate(new[k1]):
                    for k2 in copy(element):
                        # Remove 'hashKey' elements
                        # (included by Javascript)
                        if re.search(r'\$\$hashKey', k2):
                            new[k1][i].pop(k2, None)
                    if isinstance(element, dict):
                        old[k1].append(new[k1][i])
            else:
                old[k1] = new[k1]
        return old

    def _create_pipe(self):
        pipe_file = self._get_pipe_file()
        pipe = {
            'name': self._get_descriptor_name(pipe_file),
            'description': utils.read_yaml(pipe_file)
        }
        if pipe['description']['pipeline']:
            # Add module 'name' to pipeline for display in the interface
            for i, module in enumerate(pipe['description']['pipeline']):
                pipe['description']['pipeline'][i]['name'] = \
                    self._get_descriptor_name(
                        pipe['description']['pipeline'][i]['handles'])
        return pipe

    def _create_handles(self):
        handles = []
        handles_files = self._get_handles_files()
        if handles_files:
            for f in handles_files:
                h = {
                    'name': self._get_descriptor_name(f),
                    'description': utils.read_yaml(f)
                }
                handles.append(h)
        return handles

    def _create_pipe_file(self, repo_dir):
        pipe_file = os.path.join(self.project_dir, '%s.pipe' % self.pipe_name)
        pipe_skeleton = {
            'project': {
                'lib': repo_dir,
                'description': str()
            },
            'images': {
                'layers': list()
            },
            'pipeline': list()
        }

        utils.write_yaml(pipe_file, pipe_skeleton, use_ruamel=True)

    def _create_handles_folder(self):
        handles_dir = os.path.join(self.project_dir, 'handles')
        if not os.path.exists(handles_dir):
            os.mkdir(handles_dir)

    def _create_project_from_skeleton(self, skel_dir, repo_dir=None):
        pipe_file = self._get_pipe_file(skel_dir)
        if not repo_dir:
            shutil.copy(pipe_file, self.project_dir)
        else:
            pipe_content = utils.read_yaml(pipe_file, use_ruamel=True)
            pipe_content['project']['lib'] = repo_dir
            new_pipe_file = os.path.join(self.project_dir,
                                         '%s.pipe' % self.pipe_name)
            utils.write_yaml(new_pipe_file, pipe_content, use_ruamel=True)
        shutil.copytree(os.path.join(skel_dir, 'handles'),
                        os.path.join(self.project_dir, 'handles'))

    def _remove_pipe_file(self, name):
        pipe_file = os.path.join(self.project_dir, '%s.pipe' % name)
        os.remove(pipe_file)

    def _remove_handles_folder(self):
        handles_dir = os.path.join(self.project_dir, 'handles')
        shutil.rmtree(handles_dir)

    def _modify_pipe(self):
        pipe_file = self._get_pipe_file()
        # Use ruamel.yaml to preserve comments in the pipe file
        old_pipe_content = utils.read_yaml(pipe_file, use_ruamel=True)
        new_pipe_content = self.pipe['description']
        # Remove module 'name' from pipeline (only used internally)
        for i, module in enumerate(new_pipe_content['pipeline']):
            new_pipe_content['pipeline'][i].pop('name', None)
        mod_pipe_content = self._replace_values(old_pipe_content,
                                                new_pipe_content)
        utils.write_yaml(pipe_file, mod_pipe_content, use_ruamel=True)

    def _modify_handles(self):
        handles_files = []
        # Create new .handles files for added modules
        for h in self.handles:
            filename = os.path.join(self.project_dir, 'handles',
                                    '%s.handles' % h['name'])
            handles_files.append(filename)
        for i, handles_file in enumerate(handles_files):
            # If file already exists, modify its content
            if os.path.exists(handles_file):
                old_handles_content = utils.read_yaml(handles_file)
                new_handles_content = self.handles[i]['description']
                mod_handles_content = self.replace_values(old_handles_content,
                                                          new_handles_content)
            # If file doesn't yet exist, create it and add content
            else:
                mod_handles_content = self.handles[i]['description']
            utils.write_yaml(mod_handles_content, handles_file)
        # Remove .handles file that are no longer in the pipeline
        existing_handles_files = glob.glob(os.path.join(self.project_dir,
                                           'handles', '*.handles'))
        for f in existing_handles_files:
            if f not in handles_files:
                os.remove(f)

    def serialize(self):
        '''
        Serialize the attributes of the class in the format::

            {
                "experiment": str,
                "name": str,
                "pipe": {
                    "name": str,
                    "description": dict
                }
                "handles": [
                    {
                        "name": str,
                        "description": dict
                    },
                    ...
                ]
            }

        Returns
        -------
        dict
        '''
        return {
            'experiment': self.experiment,
            'name': self.pipe_name,
            'pipe': self.pipe,
            'handles': self.handles
        }

    def save(self):
        '''
        Save Jterator project:
        Update the content of *.pipe* and *.handles* files on disk
        according to modifications to the pipeline and module descriptions.
        '''
        self._modify_pipe()
        self._modify_handles()

    def create(self, repo_dir=None, skel_dir=None):
        '''
        Create a Jterator project:
        Create the project folder and an empty "handles" subfolder as well as
        a skeleton *.pipe* file, i.e. a pipeline descriptor file with all
        required main keys but an empty module list.
        When `skel_dir` is provided, the *.pipe* and *.handles* files are
        copied.

        Parameters
        ----------
        repo_dir: str, optional
            path to repository directory where module files are located
        skel_dir: str, optional
            path to repository directory that represents a project skeleton,
            i.e. contains a *.pipe* and one or more *.handles* files in a
            *handles* directory.
        '''
        if repo_dir:
            repo_dir = os.path.expandvars(repo_dir)
            repo_dir = os.path.expanduser(repo_dir)
            repo_dir = os.path.abspath(repo_dir)
        if skel_dir:
            skel_dir = os.path.expandvars(skel_dir)
            skel_dir = os.path.expanduser(skel_dir)
            skel_dir = os.path.abspath(skel_dir)
        if not os.path.exists(self.project_dir):
            os.mkdir(self.project_dir)
        if skel_dir:
            self._create_project_from_skeleton(skel_dir, repo_dir)
        else:
            self._create_pipe_file(repo_dir)
            self._create_handles_folder()

    def remove(self):
        '''
        Remove a Jterator project, i.e. kill the folder on disk.
        '''
        # remove_pipe_file(self.project_dir, self.pipe['name'])
        # remove_handles_folder(self.project_dir)
        shutil.rmtree(self.project_dir)


class JtAvailableModules(object):

    '''
    A class for holding information about available Jterator modules
    in the `JtLibrary <https://github.com/TissueMAPS/JtLibrary>`_ repository.
    '''

    def __init__(self, repo_dir):
        '''
        Initialize an instance of class JtAvailableModules.

        Parameters
        ----------
        repo_dir: str
            absolute path to the local clone of the repository
        '''
        self.repo_dir = repo_dir
        self._module_files = None
        self._handles = None
        self._module_names = None
        self._pipe_registration = None

    @property
    def module_files(self):
        '''
        Module files are assumed to reside in a subfolder called "modules"
        and have one the following suffixes: ".py", ".m", ".jl", ".r" or ".R".

        Returns
        -------
        List[str]
            paths to the module files
        '''
        if self._module_files is None:
            modules_dir = os.path.join(self.repo_dir, 'modules')
            files = [os.path.join(modules_dir, f)
                     for f in os.listdir(modules_dir)
                     if re.search(r'\.(r|R|m|jl|py)$', f)]
            self._module_files = files
        return self._module_files

    @property
    def module_names(self):
        '''
        Module names are the basenames of the `module_files`
        without the suffix.

        Returns
        -------
        List[str]
            names of the modules
        '''
        if self._module_names is None:
            names = [os.path.splitext(os.path.basename(f))[0]
                     for f in self.module_files]
            self._module_names = names
        return self._module_names

    @property
    def handles(self):
        '''
        Handles files are assumed to reside in a subfolder called "handles"
        and have the suffix ".handles".

        Returns
        -------
        dict
            handles name and description

        See also
        --------
        `create_handles`
        '''
        self._handles = create_handles(self.repo_dir)
        return self._handles

    @property
    def pipe_registration(self):
        '''
        Build pipeline elements for registration in the UI
        in the format excepted in the "pipeline" section in the `.pipe` file.

        Returns
        -------
        List[dict]
            pipeline elements
        '''
        # modules are "available" if there is a corresponding handles file
        # TODO: some checks of handles content
        available_modules = [h['name'] for h in self.handles]
        if self._pipe_registration is None:
            self._pipe_registration = list()
            for i, f in enumerate(self.module_files):
                name = self.module_names[i]
                if name in available_modules:
                    element = {
                        'name': name,
                        'description': {
                            'handles': './handles/%s.handles' % name,
                            'module': f,
                            'active': True
                        }
                    }
                    self._pipe_registration.append(element)
        return self._pipe_registration

    def serialize(self):
        '''
        Provide information in the format required by server::

            {
                "modules": list,
                "registration": list,
            }

        Returns
        -------
        dict
        '''
        return {
            'modules': self.handles,
            'registration': self.pipe_registration
        }

    @staticmethod
    def get_modules(lib_dir):
        '''
        Return a `Jtmodule` object for all available `.handles` files in the
        repository.
        '''
        return JtAvailableModules(lib_dir)