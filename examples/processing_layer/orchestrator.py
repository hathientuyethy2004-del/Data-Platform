"""
Processing Layer Orchestrator
Quản lý execution của Spark streaming và batch jobs
"""

import sys
import os
import time
import signal
import argparse
from threading import Thread, Event
from datetime import datetime
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from configs.spark_config import PROCESSING_JOBS
from configs.logging_config import setup_logger, ContextLogger

# Create logger
_base_logger = setup_logger(
    name=__name__,
    log_level=os.getenv('LOG_LEVEL', 'INFO'),
    console_output=True,
    file_output=True,
    log_file='orchestrator.log'
)

logger = ContextLogger(_base_logger)

# ============================================================================
# Processing Layer Orchestrator
# ============================================================================

class ProcessingLayerOrchestrator:
    """
    Orchestrator for PROCESSING LAYER
    - Start/manage streaming jobs
    - Schedule and run batch jobs
    - Monitor job health
    - Graceful shutdown
    """
    
    def __init__(self, enable_streaming: bool = True, enable_batch: bool = True):
        self.enable_streaming = enable_streaming
        self.enable_batch = enable_batch
        self.streaming_processes = {}
        self.batch_threads = {}
        self.shutdown_event = Event()
        
        self.stats = {
            "start_time": datetime.utcnow(),
            "jobs_started": 0,
            "jobs_completed": 0,
            "jobs_failed": 0
        }
        
        logger.info(f"🚀 Initializing PROCESSING LAYER ORCHESTRATOR")
        logger.info(f"   Streaming enabled: {enable_streaming}")
        logger.info(f"   Batch enabled: {enable_batch}")
    
    def start_streaming_job(self, job_name: str) -> bool:
        """Start a streaming job"""
        try:
            job_config = PROCESSING_JOBS.get(job_name)
            if not job_config or job_config.get("type") != "streaming":
                logger.error(f"❌ Job '{job_name}' not found or not a streaming job")
                return False
            
            if not job_config.get("enabled", True):
                logger.warning(f"⚠️  Job '{job_name}' is disabled")
                return False
            
            logger.info(f"\n📌 Starting streaming job: {job_name}")
            logger.info(f"   Description: {job_config.get('description', 'N/A')}")
            
            # Map job name to module
            module_map = {
                "event_aggregation": "jobs.streaming.event_aggregation",
                "clickstream_analysis": "jobs.streaming.clickstream_analysis",
                "data_enrichment": "jobs.streaming.data_enrichment",
                "cdc_transformation": "jobs.streaming.cdc_transformation"
            }
            
            module_name = module_map.get(job_name)
            if not module_name:
                logger.error(f"❌ No module mapping for job: {job_name}")
                return False
            
            # Start job in subprocess
            script_path = os.path.join(
                os.path.dirname(__file__),
                module_name.replace(".", "/") + ".py"
            )
            
            logger.info(f"   Script: {script_path}")
            
            try:
                process = subprocess.Popen(
                    [sys.executable, script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                self.streaming_processes[job_name] = process
                self.stats["jobs_started"] += 1
                
                logger.info(f"✅ Streaming job '{job_name}' started (PID: {process.pid})")
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to start streaming job '{job_name}': {e}")
                self.stats["jobs_failed"] += 1
                return False
        
        except Exception as e:
            logger.error(f"❌ Error in start_streaming_job: {e}")
            return False
    
    def start_batch_job(self, job_name: str, job_args: dict = None) -> bool:
        """Start a batch job in background thread"""
        try:
            job_config = PROCESSING_JOBS.get(job_name)
            if not job_config or job_config.get("type") != "batch":
                logger.error(f"❌ Job '{job_name}' not found or not a batch job")
                return False
            
            if not job_config.get("enabled", True):
                logger.warning(f"⚠️  Job '{job_name}' is disabled")
                return False
            
            logger.info(f"\n📌 Starting batch job: {job_name}")
            logger.info(f"   Description: {job_config.get('description', 'N/A')}")
            
            # Map job name to module
            module_map = {
                "hourly_aggregate": "jobs.batch.hourly_aggregate",
                "daily_summary": "jobs.batch.daily_summary",
                "user_segment": "jobs.batch.user_segmentation"
            }
            
            module_name = module_map.get(job_name)
            if not module_name:
                logger.error(f"❌ No module mapping for job: {job_name}")
                return False
            
            # Start job in subprocess with arguments
            script_path = os.path.join(
                os.path.dirname(__file__),
                module_name.replace(".", "/") + ".py"
            )
            
            args = [sys.executable, script_path]
            if job_args:
                for key, value in job_args.items():
                    args.append(f"--{key}")
                    args.append(str(value))
            
            logger.info(f"   Script: {script_path}")
            
            try:
                process = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                self.batch_threads[job_name] = process
                self.stats["jobs_started"] += 1
                
                logger.info(f"✅ Batch job '{job_name}' started (PID: {process.pid})")
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to start batch job '{job_name}': {e}")
                self.stats["jobs_failed"] += 1
                return False
        
        except Exception as e:
            logger.error(f"❌ Error in start_batch_job: {e}")
            return False
    
    def start_all(self):
        """Start all enabled jobs"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 STARTING PROCESSING LAYER")
        logger.info(f"{'='*70}\n")
        
        # Start streaming jobs
        if self.enable_streaming:
            streaming_jobs = [
                name for name, cfg in PROCESSING_JOBS.items()
                if cfg.get("type") == "streaming" and cfg.get("enabled", True)
            ]
            
            logger.info(f"📡 Streaming jobs to start: {streaming_jobs}")
            for job_name in streaming_jobs:
                self.start_streaming_job(job_name)
                time.sleep(1)  # Stagger job starts
        
        # Start initial batch jobs
        if self.enable_batch:
            initial_batch_jobs = ["hourly_aggregate", "daily_summary"]
            logger.info(f"⚙️  Initial batch jobs to start: {initial_batch_jobs}")
            for job_name in initial_batch_jobs:
                self.start_batch_job(job_name)
                time.sleep(0.5)
        
        logger.info(f"\n✅ All jobs started!\n")
        
        # Start monitoring thread
        monitor_thread = Thread(
            target=self._monitoring_loop,
            daemon=False,
            name="orchestrator-monitor"
        )
        monitor_thread.start()
    
    def _monitoring_loop(self):
        """Monitor loop - check job health"""
        logger.info("🔍 Starting monitoring loop")
        
        while not self.shutdown_event.is_set():
            try:
                time.sleep(30)  # Check every 30 seconds
                
                # Check streaming jobs
                dead_streaming_jobs = []
                for job_name, process in self.streaming_processes.items():
                    if process.poll() is not None:  # Process has exited
                        dead_streaming_jobs.append(job_name)
                        self.stats["jobs_failed"] += 1
                        logger.warning(f"⚠️  Streaming job '{job_name}' died (exit code: {process.returncode})")
                
                # Check batch jobs
                dead_batch_jobs = []
                for job_name, process in self.batch_threads.items():
                    if process.poll() is not None:
                        dead_batch_jobs.append(job_name)
                        self.stats["jobs_completed"] += 1
                        logger.info(f"✅ Batch job '{job_name}' completed (exit code: {process.returncode})")
                
                # Remove dead jobs
                for job_name in dead_streaming_jobs:
                    del self.streaming_processes[job_name]
                
                for job_name in dead_batch_jobs:
                    del self.batch_threads[job_name]
                
                # Log stats periodically
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    logger.info(
                        f"📊 Orchestrator Stats: "
                        f"streaming={len(self.streaming_processes)}, "
                        f"batch={len(self.batch_threads)}, "
                        f"started={self.stats['jobs_started']}, "
                        f"completed={self.stats['jobs_completed']}, "
                        f"failed={self.stats['jobs_failed']}"
                    )
            
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
    
    def stop_all(self):
        """Stop all running jobs"""
        logger.info(f"\n{'='*70}")
        logger.info(f"⏹️  STOPPING PROCESSING LAYER")
        logger.info(f"{'='*70}\n")
        
        # Signal shutdown
        self.shutdown_event.set()
        
        # Stop streaming jobs
        for job_name, process in list(self.streaming_processes.items()):
            logger.info(f"Stopping streaming job: {job_name}")
            try:
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"✅ Streaming job '{job_name}' stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping streaming job '{job_name}': {e}")
                try:
                    process.kill()
                except:
                    pass
        
        # Stop batch jobs
        for job_name, process in list(self.batch_threads.items()):
            logger.info(f"Stopping batch job: {job_name}")
            try:
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"✅ Batch job '{job_name}' stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping batch job '{job_name}': {e}")
                try:
                    process.kill()
                except:
                    pass
        
        self._print_final_stats()
    
    def _print_final_stats(self):
        """Print final statistics"""
        uptime = datetime.utcnow() - self.stats["start_time"]
        
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 FINAL STATISTICS")
        logger.info(f"{'='*70}")
        logger.info(f"Uptime: {uptime.total_seconds():.0f} seconds")
        logger.info(f"Jobs started: {self.stats['jobs_started']}")
        logger.info(f"Jobs completed: {self.stats['jobs_completed']}")
        logger.info(f"Jobs failed: {self.stats['jobs_failed']}")
        logger.info(f"{'='*70}\n")
    
    def handle_signal(self, signum, frame):
        """Handle SIGTERM/SIGINT"""
        logger.info(f"\n📬 Received signal {signum}, shutting down gracefully...")
        self.stop_all()
        sys.exit(0)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Processing Layer Orchestrator")
    parser.add_argument(
        "--streaming",
        type=bool,
        default=True,
        help="Enable streaming jobs (default: True)"
    )
    parser.add_argument(
        "--batch",
        type=bool,
        default=True,
        help="Enable batch jobs (default: True)"
    )
    
    args = parser.parse_args()
    
    orchestrator = ProcessingLayerOrchestrator(
        enable_streaming=args.streaming,
        enable_batch=args.batch
    )
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, orchestrator.handle_signal)
    signal.signal(signal.SIGINT, orchestrator.handle_signal)
    
    try:
        # Start all jobs
        orchestrator.start_all()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\n⏹️  Keyboard interrupt, shutting down...")
        orchestrator.stop_all()
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        orchestrator.stop_all()
        sys.exit(1)


if __name__ == "__main__":
    main()
