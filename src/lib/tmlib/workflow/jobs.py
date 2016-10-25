import logging
from abc import ABCMeta
from abc import abstractproperty
import gc3libs
# from abc import abstractmethod
# from gc3libs.workflow import RetryableTask
from gc3libs.workflow import AbortOnError
from gc3libs.workflow import SequentialTaskCollection
from gc3libs.workflow import ParallelTaskCollection

from tmlib.utils import create_datetimestamp

logger = logging.getLogger(__name__)


class Job(gc3libs.Application):

    '''Abstract base class for a job, which can be submitted for processing
    on different cluster backends.
    '''

    def __init__(self, arguments, output_dir, submission_id, user_name):
        '''
        Parameters
        ----------
        arguments: List[str]
            command line arguments
        output_dir: str
            absolute path to the output directory, where log reports will
            be stored
        submission_id: int
            ID of the corresponding submission
        user_name: str
            name of the submitting user
        '''
        t = create_datetimestamp()
        self.user_name = user_name
        self.submission_id = submission_id
        super(Job, self).__init__(
            jobname=self.name,
            arguments=arguments,
            output_dir=output_dir,
            stdout='%s_%s.out' % (self.name, t),
            stderr='%s_%s.err' % (self.name, t),
            # Assumes that nodes have access to a shared file system.
            inputs=[],
            outputs=[],
        )

    def sbatch(self, resource, **kwargs):
        '''Overwrites the original `sbatch` method to enable
        `fair-share scheduling on SLURM backends <http://slurm.schedmd.com/priority_multifactor.html>`_.

        See also
        --------
        :method:`gc3libs.Application.sbatch`

        Note
        ----
        User accounts must be registered in the
        `SLURM accounting database <http://slurm.schedmd.com/accounting.html>`_.
        '''
        sbatch, cmdline = super(Job, self).sbatch(resource, **kwargs)
        sbatch = sbatch[:1] + ['--account', self.user_name] + sbatch[1:]
        return (sbatch, cmdline)

    @abstractproperty
    def name(self):
        '''str: name of the job
        '''
        pass

    def retry(self):
        '''Decides whether the job should be retried.

        Returns
        -------
        bool
            whether job should be resubmitted
        '''
        # TODO
        return super(self.__class__, self).retry()

    @property
    def is_terminated(self):
        '''bool: whether the job is in state TERMINATED
        '''
        return self.execution.state == gc3libs.Run.State.TERMINATED

    @property
    def is_running(self):
        '''bool: whether the job is in state RUNNING
        '''
        return self.execution.state == gc3libs.Run.State.RUNNING

    @property
    def is_stopped(self):
        '''bool: whether the job is in state STOPPED
        '''
        return self.execution.state == gc3libs.Run.State.STOPPED

    @property
    def is_submitted(self):
        '''bool: whether the job is in state SUBMITTED
        '''
        return self.execution.state == gc3libs.Run.State.SUBMITTED

    @property
    def is_new(self):
        '''bool: whether the job is in state NEW
        '''
        return self.execution.state == gc3libs.Run.State.NEW


class WorkflowStepJob(Job):

    '''Abstract base class for an individual job as part of
    workflow step phase.

    Note
    ----
    Jobs are constructed based on job descriptions, which persist on disk
    in form of JSON files.
    '''

    # TODO: inherit from RetryableTask(max_retries=1) and implement
    # re-submission logic by overwriting retry() method:
    # 
    #     with open(err_file, 'r') as err:
    #         if re.search(r'^FAILED', err, re.MULTILINE):
    #             reason = 'Exception'
    #         elif re.search(r'^TIMEOUT', err, re.MULTILINE):
    #             reason = 'Timeout'
    #         elif re.search(r'^[0-9]*\s*\bKilled\b', err, re.MULTILINE):
    #             reason = 'Memory'
    #         else:
    #             reason = 'Unknown'

    __metaclass__ = ABCMeta

    def __init__(self, step_name, arguments, output_dir,
            submission_id, user_name):
        '''
        Parameters
        ----------
        step_name: str
            name of the corresponding TissueMAPS workflow step
        arguments: List[str]
            command line arguments
        output_dir: str
            absolute path to the output directory, where log reports will
            be stored
        submission_id: int
            ID of the corresponding submission
        user_name: str
            name of the submitting user

        See also
        --------
        :class:`tmlib.models.Submission`

        Note
        ----
        When submitting with `SLURM` backend, there must be an existing account
        for `user_name`.
        '''
        self.step_name = step_name
        super(WorkflowStepJob, self).__init__(
            arguments, output_dir, submission_id, user_name
        )


class InitJob(WorkflowStepJob):

    '''Class for a *init* jobs, which creates the descriptions for the
    subsequent *run* and *collect* phases.
    '''

    def __init__(self, step_name, arguments, output_dir, submission_id, user_name):
        '''
        Parameters
        ----------
        step_name: str
            name of the corresponding TissueMAPS workflow step
        arguments: List[str]
            command line arguments
        output_dir: str
            absolute path to the output directory, where log reports will
            be stored
        submission_id: int
            ID of the corresponding submission
        user_name: str
            name of the submitting user
        '''
        super(self.__class__, self).__init__(
            step_name=step_name,
            arguments=arguments,
            output_dir=output_dir,
            submission_id=submission_id,
            user_name=user_name
        )

    @property
    def name(self):
        '''str:name of the job'''
        return '%s_init' % self.step_name

    def __repr__(self):
        return (
            '<%s(name=%r, submission_id=%r)>'
            % (self.__class__.__name__, self.name, self.submission_id)
        )


class RunJob(WorkflowStepJob):

    '''
    Class for TissueMAPS run jobs, which can be processed in parallel.
    '''

    def __init__(self, step_name, arguments, output_dir, job_id,
                 submission_id, user_name, index=None):
        '''
        Initialize an instance of class RunJob.

        Parameters
        ----------
        step_name: str
            name of the corresponding TissueMAPS workflow step
        arguments: List[str]
            command line arguments
        output_dir: str
            absolute path to the output directory, where log reports will
            be stored
        job_id: int
            one-based job identifier number
        submission_id: int
            ID of the corresponding submission
        index: int, optional
            index of the *run* job collection in case the step has multiple
            *run* phases
        '''
        self.job_id = job_id
        if not isinstance(index, int) and index is not None:
            raise TypeError('Argument "index" must have type int.')
        self.index = index
        super(self.__class__, self).__init__(
            step_name=step_name,
            arguments=arguments,
            output_dir=output_dir,
            submission_id=submission_id,
            user_name=user_name
        )

    @property
    def name(self):
        '''str: name of the job
        '''
        if self.index is None:
            return '%s_run_%.6d' % (self.step_name, self.job_id)
        else:
            return (
                '%s_run-%.2d_%.6d' % (self.step_name, self.index, self.job_id)
            )

    def __repr__(self):
        return (
            '<%s(name=%r, submission_id=%r)>'
            % (self.__class__.__name__, self.name, self.submission_id)
        )


class CollectJob(WorkflowStepJob):

    '''Class for a collect jobs, which can be processed once all
    parallel jobs are successfully completed.
    '''

    def __init__(self, step_name, arguments, output_dir, submission_id, user_name):
        '''
        Parameters
        ----------
        step_name: str
            name of the corresponding TissueMAPS workflow step
        arguments: List[str]
            command line arguments
        output_dir: str
            absolute path to the output directory, where log reports will
            be stored
        submission_id: int
            ID of the corresponding submission
        user_name: str
            name of the submitting user
        '''
        super(self.__class__, self).__init__(
            step_name=step_name,
            arguments=arguments,
            output_dir=output_dir,
            submission_id=submission_id,
            user_name=user_name
        )

    @property
    def name(self):
        '''str:name of the job'''
        return '%s_collect' % self.step_name

    def __repr__(self):
        return (
            '<%s(name=%r, submission_id=%r)>'
            % (self.__class__.__name__, self.name, self.submission_id)
        )


class JobCollection(object):

    '''Abstract base class for job collections.'''

    __metaclass__ = ABCMeta


class RunJobCollection(JobCollection):

    '''Abstract base class for run job collections.'''

    __metaclass__ = ABCMeta


class SingleRunJobCollection(ParallelTaskCollection, RunJobCollection):

    '''Class for a single run job collection.'''

    def __init__(self, step_name, submission_id, jobs=None, index=None):
        '''
        Parameters
        ----------
        step_name: str
            name of the corresponding TissueMAPS workflow step
        submission_id: int
            ID of the corresponding submission
        jobs: List[tmlibs.workflow.jobs.RunJob], optional
            list of jobs that should be processed (default: ``None``)
        index: int, optional
            index of the *run* job collection in case the step has multiple
            *run* phases
        '''
        self.step_name = step_name
        if jobs is not None:
            if not isinstance(jobs, list):
                raise TypeError('Argument "jobs" must have type list.')
            if not all([isinstance(j, RunJob) for j in jobs]):
                raise TypeError(
                    'Elements of argument "jobs" must have type '
                    'tmlib.workflow.jobs.RunJob'
                )
        if index is None:
            self.name = '%s_run' % self.step_name
        else:
            if not isinstance(index, int):
                raise TypeError('Argument "index" must have type int.')
            self.name = '%s_run-%.2d' % (self.step_name, index)
        self.submission_id = submission_id
        super(self.__class__, self).__init__(jobname=self.name, tasks=jobs)

    def add(self, job):
        '''Adds a job to the collection.

        Parameters
        ----------
        job: tmlibs.workflow.jobs.RunJob
            job that should be added

        Raises
        ------
        TypeError
            when `job` has wrong type
        '''
        if not isinstance(job, RunJob):
            raise TypeError(
                'Argument "job" must have type '
                'tmlib.workflow.jobs.RunJob'
            )
        super(self.__class__, self).add(job)

    def __repr__(self):
        return (
            '<%s(name=%r, n=%r, submission_id=%r)>'
            % (self.__class__.__name__, self.name, len(self.tasks),
                self.submission_id)
        )


class MultiRunJobCollection(AbortOnError, SequentialTaskCollection, RunJobCollection):

    '''Class for multiple run job collections.'''

    def __init__(self, step_name, submission_id, run_job_collections=None):
        '''
        Parameters
        ----------
        step_name: str
            name of the corresponding TissueMAPS workflow step
        submission_id: int
            ID of the corresponding submission
        run_job_collections: List[tmlib.workflow.jobs.SingleRunJobCollection], optional
            collections of run jobs that should be processed one after another
        '''
        self.name = '%s_run' % step_name
        self.step_name = step_name
        self.submission_id = submission_id
        super(self.__class__, self).__init__(
            jobname=self.name, tasks=run_job_collections
        )

    def add(self, run_job_collection):
        '''Add a collection of run jobs.

        Parameters
        ----------
        run_job_collection: tmlib.workflow.jobs.SingleRunJobCollection
            collection of run jobs that should be added

        Raises
        ------
        TypeError
            when `run_job_collection` has wrong type
        '''
        if not isinstance(run_job_collection, SingleRunJobCollection):
            raise TypeError(
                'Argument "run_job_collection" must have type '
                'tmlib.workflow.jobs.SingleRunJobCollection'
            )
        super(self.__class__, self).add(run_job_collection)

    def __repr__(self):
        return (
            '<%s(name=%r, n=%r, submission_id=%r)>'
            % (self.__class__.__name__, self.name, len(self.tasks),
                self.submission_id)
        )


class CliJobCollection(SequentialTaskCollection, JobCollection):

    '''Class for manual submission of the *run* and *collect* phases of a
    workflow steps via
    :method:`tmlib.workflow.cli.CommandLineInterface.submit`.
    '''

    def __init__(self, step_name, submission_id, jobs=None):
        '''
        Parameters
        ----------
        step_name: str
            name of the corresponding TissueMAPS workflow step
        submission_id: int
            ID of the corresponding submission
        jobs: List[tmlibs.workflow.jobs.RunJobCollection or tmlibs.workflow.jobs.CollectJob], optional
            list of jobs that should be processed (default: ``None``)
        '''
        self.submission_id = submission_id
        if jobs is not None:
            if not isinstance(jobs[0], RunJobCollection):
                raise TypeError(
                    'First job must have type '
                    'tmlib.workflow.jobs.RunJobCollection.'
                )
        super(self.__class__, self).__init__(jobname=step_name, tasks=jobs)