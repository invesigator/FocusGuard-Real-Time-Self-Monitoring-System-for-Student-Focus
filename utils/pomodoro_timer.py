# pomodoro_timer.py
import time
from threading import Thread
import logging
from datetime import datetime, timedelta

class PomodoroTimer:
    def __init__(self, audio_manager):
        self.audio_manager = audio_manager
        
        # Default Pomodoro settings (in minutes)
        self.work_duration = 25
        self.short_break_duration = 5
        self.long_break_duration = 15
        self.long_break_interval = 4  # Number of work sessions before long break
        
        # Timer state
        self.is_active = False
        self.is_paused = False
        self.current_session = 0  # Track completed work sessions
        self.time_remaining = 0
        self.session_end_time = None
        self.timer_thread = None
        self.session_type = "work"  # "work", "short_break", or "long_break"
        
    def start_timer(self):
        """Start or resume the Pomodoro timer"""
        if not self.is_active:
            self.is_active = True
            self.is_paused = False
            self.start_work_session()
        elif self.is_paused:
            self.is_paused = False
            self.session_end_time = datetime.now() + timedelta(seconds=self.time_remaining)
            self._start_timer_thread()
            
    def pause_timer(self):
        """Pause the current timer session"""
        if self.is_active and not self.is_paused:
            self.is_paused = True
            if self.session_end_time:
                self.time_remaining = (self.session_end_time - datetime.now()).total_seconds()
                
    def stop_timer(self):
        """Stop the timer completely"""
        self.is_active = False
        self.is_paused = False
        self.current_session = 0
        self.time_remaining = 0
        self.session_end_time = None
        self.session_type = "work"
        
    def start_work_session(self):
        """Start a work session"""
        self.session_type = "work"
        duration = self.work_duration * 60  # Convert to seconds
        self.time_remaining = duration
        self.session_end_time = datetime.now() + timedelta(seconds=duration)
        self._start_timer_thread()
        
    def start_break(self):
        """Start appropriate break based on completed sessions"""
        self.current_session += 1
        
        if self.current_session % self.long_break_interval == 0:
            self.session_type = "long_break"
            duration = self.long_break_duration * 60
        else:
            self.session_type = "short_break"
            duration = self.short_break_duration * 60
            
        self.time_remaining = duration
        self.session_end_time = datetime.now() + timedelta(seconds=duration)
        
    def _start_timer_thread(self):
        """Start the timer thread"""
        if self.timer_thread and self.timer_thread.is_alive():
            return
            
        self.timer_thread = Thread(target=self._timer_loop)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        
    # Modified _timer_loop method with smart session control
    def _timer_loop(self):
        """Main timer loop with smart session transitions"""
        while self.is_active and not self.is_paused:
            if not self.session_end_time:
                break

            remaining = (self.session_end_time - datetime.now()).total_seconds()
            
            if remaining <= 0:
                # Session completed, check what type it was
                if self.session_type == "work":
                    # If it was a work session, follow Pomodoro technique with automatic transition
                    self.audio_manager.play_alarm("work_complete", True)
                    self.start_break()  # Automatically start appropriate break
                else:
                    # If it was a break session, check if it was manually selected
                    self.audio_manager.play_alarm("break_complete", True)
                    
                    # Check if this break was part of a Pomodoro sequence or manually selected
                    if hasattr(self, 'manually_selected_break') and self.manually_selected_break:
                        # Manually selected break - stop timer after completion
                        self.is_active = False
                        self.time_remaining = 0
                        # Don't forget to reset the flag for next time
                        self.manually_selected_break = False
                        break  # Exit the timer loop
                    else:
                        # This was a break in a Pomodoro sequence, transition to work
                        self.session_type = "work"
                        duration = self.work_duration * 60
                        self.time_remaining = duration
                        self.session_end_time = datetime.now() + timedelta(seconds=duration)
                
                # Continue to next iteration
                continue
                    
            self.time_remaining = remaining
            time.sleep(0.1)  # Reduce CPU usage

    # Add these methods to PomodoroTimer class
    def start_custom_session(self, session_type):
        """Start a custom session with the specified type"""
        if session_type == "work":
            self.session_type = "work"
            duration = self.work_duration * 60
            self.manually_selected_break = False  # Not a break
        elif session_type == "short_break":
            self.session_type = "short_break"
            duration = self.short_break_duration * 60
            self.manually_selected_break = True  # Manually selected break
        elif session_type == "long_break":
            self.session_type = "long_break"
            duration = self.long_break_duration * 60
            self.manually_selected_break = True  # Manually selected break
        else:
            # Default to work
            self.session_type = "work"
            duration = self.work_duration * 60
            self.manually_selected_break = False
        
        self.is_active = True
        self.is_paused = False
        self.time_remaining = duration
        self.session_end_time = datetime.now() + timedelta(seconds=duration)
        self._start_timer_thread()
            
    def get_timer_status(self):
        """Return current timer status for UI display"""
        if not self.is_active:
            return {
                "active": False,
                "time_remaining": "00:00",
                "session_type": "inactive",
                "sessions_completed": self.current_session
            }
            
        minutes = int(self.time_remaining // 60)
        seconds = int(self.time_remaining % 60)
        
        return {
            "active": True,
            "paused": self.is_paused,
            "time_remaining": f"{minutes:02d}:{seconds:02d}",
            "session_type": self.session_type,
            "sessions_completed": self.current_session
        }
        
    def set_durations(self, work=25, short_break=5, long_break=15, long_break_interval=4):
        """Update timer durations (in minutes)"""
        self.work_duration = work
        self.short_break_duration = short_break
        self.long_break_duration = long_break
        self.long_break_interval = long_break_interval