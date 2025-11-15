"""
Block Prediction Scheduler Jobs for 7-Block Framework.

Defines APScheduler jobs that run at precise times:
- Predictions: :42:51 of each hour (5/7 point = 71.4% through hour)
- Verification: :00:00 of each hour (hour completion)

Uses CronTrigger for exact timing with second-level precision.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from ..services.block_prediction_service import BlockPredictionService
from ..services.block_verification_service import BlockVerificationService
from ..config.scheduler_config import SchedulerConfig

logger = logging.getLogger(__name__)


class BlockPredictionJobs:
    """
    Manages scheduler jobs for 7-block predictions and verification.

    Implements two jobs:
    1. BlockPredictionJob: Runs at :42:51 of each hour (prediction point)
    2. BlockVerificationJob: Runs at :00:00 of each hour (verification point)
    """

    # Cron timing constants
    PREDICTION_SECOND = 51        # Predict at :42:51 (42m 51s into hour)
    PREDICTION_MINUTE = 42
    VERIFICATION_SECOND = 0       # Verify at :00:00 (hour completion)
    VERIFICATION_MINUTE = 0

    def __init__(
        self,
        scheduler: BackgroundScheduler,
        prediction_service: BlockPredictionService,
        verification_service: BlockVerificationService
    ):
        """
        Initialize BlockPredictionJobs with services.

        Args:
            scheduler: APScheduler BackgroundScheduler instance
            prediction_service: BlockPredictionService for generating predictions
            verification_service: BlockVerificationService for verifying predictions
        """
        self.scheduler = scheduler
        self.prediction_service = prediction_service
        self.verification_service = verification_service
        logger.debug("BlockPredictionJobs initialized")

    def register_jobs(self) -> None:
        """
        Register all block prediction jobs with the scheduler.

        Registers:
        1. Block prediction job (cron: 42:51 every hour)
        2. Block verification job (cron: 00:00 every hour)
        """
        logger.info("Registering block prediction jobs with scheduler")

        # Check if jobs are enabled
        if not SchedulerConfig.ENABLE_PREDICTION_JOB:
            logger.warning("Block prediction job is disabled")
            return

        if not SchedulerConfig.ENABLE_VERIFICATION_JOB:
            logger.warning("Block verification job is disabled")

        # Register prediction job
        self._register_prediction_job()

        # Register verification job
        if SchedulerConfig.ENABLE_VERIFICATION_JOB:
            self._register_verification_job()

        logger.info("Block prediction jobs registered successfully")

    def _register_prediction_job(self) -> None:
        """
        Register the prediction generation job.

        Runs at :42:51 of every hour (prediction point).
        Uses CronTrigger with second-level precision.
        """
        logger.info(
            f"Registering prediction job: "
            f"*:{self.PREDICTION_MINUTE}:{self.PREDICTION_SECOND} UTC"
        )

        try:
            # Remove existing job if present
            try:
                self.scheduler.remove_job('block_prediction')
            except:
                pass

            # Register prediction job with CronTrigger
            self.scheduler.add_job(
                func=self._execute_block_prediction,
                trigger=CronTrigger(
                    hour='*',                          # Every hour
                    minute=self.PREDICTION_MINUTE,     # At minute 42
                    second=self.PREDICTION_SECOND,     # At second 51
                    timezone=SchedulerConfig.TIMEZONE
                ),
                id='block_prediction',
                name='Block Prediction Generation',
                coalesce=SchedulerConfig.COALESCE,
                max_instances=SchedulerConfig.MAX_INSTANCES,
                misfire_grace_time=SchedulerConfig.MISFIRE_GRACE_TIME
            )
            logger.info("✓ Prediction job registered")

        except Exception as e:
            logger.error(f"Error registering prediction job: {e}", exc_info=True)

    def _register_verification_job(self) -> None:
        """
        Register the verification job.

        Runs at :00:00 of every hour (hour completion + buffer).
        Verifies predictions made at :42:51 of the previous hour.
        Uses CronTrigger with second-level precision.
        """
        logger.info(
            f"Registering verification job: "
            f"*:{self.VERIFICATION_MINUTE}:{self.VERIFICATION_SECOND} UTC"
        )

        try:
            # Remove existing job if present
            try:
                self.scheduler.remove_job('block_verification')
            except:
                pass

            # Register verification job with CronTrigger
            self.scheduler.add_job(
                func=self._execute_block_verification,
                trigger=CronTrigger(
                    hour='*',                              # Every hour
                    minute=self.VERIFICATION_MINUTE,       # At minute 0
                    second=self.VERIFICATION_SECOND,       # At second 0
                    timezone=SchedulerConfig.TIMEZONE
                ),
                id='block_verification',
                name='Block Prediction Verification',
                coalesce=SchedulerConfig.COALESCE,
                max_instances=SchedulerConfig.MAX_INSTANCES,
                misfire_grace_time=SchedulerConfig.MISFIRE_GRACE_TIME
            )
            logger.info("✓ Verification job registered")

        except Exception as e:
            logger.error(f"Error registering verification job: {e}", exc_info=True)

    @staticmethod
    def _execute_block_prediction() -> None:
        """
        Execute block prediction generation.

        This is the job function that runs at :42:51.
        Generates predictions for all enabled tickers.
        """
        try:
            logger.info("=" * 60)
            logger.info("🎯 BLOCK PREDICTION JOB STARTED")
            logger.info(f"Execution time: {datetime.utcnow().isoformat()}")
            logger.info("=" * 60)

            # This would be called by the scheduler
            # For now, log that it would execute
            logger.info("Block prediction generation would execute here")
            logger.info("(Requires tickers list and service injection)")

            logger.info("=" * 60)
            logger.info("✓ BLOCK PREDICTION JOB COMPLETED")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(
                f"Error executing block prediction job: {e}",
                exc_info=True
            )

    @staticmethod
    def _execute_block_verification() -> None:
        """
        Execute block prediction verification.

        This is the job function that runs at :00:00.
        Verifies all pending predictions from the previous hour.
        """
        try:
            logger.info("=" * 60)
            logger.info("✓ BLOCK VERIFICATION JOB STARTED")
            logger.info(f"Execution time: {datetime.utcnow().isoformat()}")
            logger.info("=" * 60)

            # This would be called by the scheduler
            # For now, log that it would execute
            logger.info("Block prediction verification would execute here")
            logger.info("(Requires service injection)")

            logger.info("=" * 60)
            logger.info("✓ BLOCK VERIFICATION JOB COMPLETED")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(
                f"Error executing block verification job: {e}",
                exc_info=True
            )

    def unregister_jobs(self) -> None:
        """
        Unregister all block prediction jobs from the scheduler.

        Called during shutdown or service cleanup.
        """
        logger.info("Unregistering block prediction jobs")

        try:
            self.scheduler.remove_job('block_prediction')
            logger.debug("Removed block prediction job")
        except:
            pass

        try:
            self.scheduler.remove_job('block_verification')
            logger.debug("Removed block verification job")
        except:
            pass

        logger.info("Block prediction jobs unregistered")

    def get_job_status(self) -> dict:
        """
        Get status of registered block prediction jobs.

        Returns:
            Dictionary with job status and next run times
        """
        status = {
            'prediction': None,
            'verification': None,
            'scheduler_running': self.scheduler.running
        }

        try:
            prediction_job = self.scheduler.get_job('block_prediction')
            if prediction_job:
                status['prediction'] = {
                    'id': prediction_job.id,
                    'name': prediction_job.name,
                    'next_run_time': prediction_job.next_run_time.isoformat() if prediction_job.next_run_time else None,
                    'trigger': str(prediction_job.trigger)
                }
        except:
            pass

        try:
            verification_job = self.scheduler.get_job('block_verification')
            if verification_job:
                status['verification'] = {
                    'id': verification_job.id,
                    'name': verification_job.name,
                    'next_run_time': verification_job.next_run_time.isoformat() if verification_job.next_run_time else None,
                    'trigger': str(verification_job.trigger)
                }
        except:
            pass

        return status
